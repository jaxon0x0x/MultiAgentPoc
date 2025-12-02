import json
import os
import logging
import smtplib
import asyncio
from typing import Annotated
from email.mime.text import MIMEText
from livekit.agents import llm
import geocoder

# Assumed external modules (keep these if you have them)
from db_driver import DatabaseDriver
from rag_engine import RAG_ENGINE

logger = logging.getLogger("api")
logger.setLevel(logging.INFO)

DB = DatabaseDriver()

# Service normalization mapping
SERVICE_MAPPING = {
    "ambulance": "hospital",
    "medical": "hospital",
    "hospital": "hospital",
    "fire": "firestation",
    "police": "policestation"
}

# Normalize service names to standard keys
def _normalize_service(value: str) -> str | None:
    for key, mapped in SERVICE_MAPPING.items():
        if key in value.lower(): return mapped
    return None

# Get email for service based on city and optional coordinates
def _get_email_for_service(service: str, city: str, lat: float = None, lng: float = None) -> str | None:
    mapped = _normalize_service(service)
    if not mapped: return None

    # 1. Try exact city match
    email = DB.get_service_email(mapped, city)
    if email: return email

    # 2. Try reverse geocoding if coords exist
    if lat and lng:
        try:
            geo = geocoder.osm([lat, lng], method="reverse")
            if geo.city: return DB.get_service_email(mapped, geo.city)
        except:
            pass

    # 3. Fallback
    return DB.get_service_email(mapped)

# Send email synchronously (to be called in async thread)
def _send_email_sync(to: str, subject: str, body: str):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = os.getenv("SMTP_FROM", "112@emergency.local")
    msg["To"] = to

    use_ssl = os.getenv("SMTP_USE_SSL", "false").lower() == "true"
    cls = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP

    with cls(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT", 587))) as server:
        if not use_ssl: server.starttls()
        server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD"))
        server.sendmail(msg["From"], [to], msg.as_string())

# Inherit from FunctionContext to define tool functions
class AssistantFnc(llm.FunctionContext):
    def __init__(self):
        super().__init__()
        self._latest_lat: float | None = None
        self._latest_lng: float | None = None
        self._latest_analysis: str | None = None

    def set_photo_analysis(self, text: str):
        self._latest_analysis = text
        logger.info(f"Analysis stored in memory ({len(text)} chars)")

    def update_location(self, lat: float, lng: float):
        self._latest_lat = lat
        self._latest_lng = lng

    @llm.ai_callable(description="Consult emergency guidelines.")
    async def consult_guidelines(self, query: Annotated[str, llm.TypeInfo(description="Topic")]):
        return RAG_ENGINE.search(query) or "No guidelines found."

    @llm.ai_callable(description="Save image URL.")
    async def save_image_url(self, url: Annotated[str, llm.TypeInfo(description="Image URL")]):
        logger.info(f"Image saved: {url}")
        return "Image stored."

    @llm.ai_callable(description="Send incident report to emergency services.")
    async def send_incident_note(
            self,
            incident_type: Annotated[str, llm.TypeInfo(description="Type of emergency")],
            city: Annotated[str, llm.TypeInfo(description="City")],
            location: Annotated[str, llm.TypeInfo(description="Address")],
            casualties: Annotated[str, llm.TypeInfo(description="Casualties info")],
            details: Annotated[str, llm.TypeInfo(description="Details")],
            recommended_service: Annotated[str, llm.TypeInfo(description="Service to notify")],
            coordinates: Annotated[str, llm.TypeInfo(description="Lat,Lng")] = "",
            photo_summary: Annotated[str, llm.TypeInfo(description="Ignored, system uses file")] = "",
    ):
        # 1. Resolve Location
        final_coords = coordinates
        if not final_coords and self._latest_lat:
            final_coords = f"{self._latest_lat}, {self._latest_lng}"

        # 2. FORCE USE OF STORED ANALYSIS (Prevent Hallucination)
        final_photo = photo_summary
        if self._latest_analysis:
            final_photo = self._latest_analysis
            logger.info("Using stored FORENSIC ANALYSIS from file.")

        incident = {
            "type": incident_type, "city": city, "address": location,
            "coords": final_coords, "casualties": casualties, "details": details,
            "photo_analysis": final_photo, "service": recommended_service
        }

        # 3. Find Email
        lat, lng = (float(x) for x in final_coords.split(",")) if "," in final_coords else (None, None)
        email = _get_email_for_service(recommended_service, city, lat, lng)

        if not email:
            return f"Error: No email found for {recommended_service} in {city}."

        # 4. Send Email (Non-blocking)
        try:
            await asyncio.to_thread(_send_email_sync, email, f"112 Alert: {incident_type}",
                                    json.dumps(incident, indent=2))
            return f"Report sent to {email}."
        except Exception as e:
            logger.error(f"Email failed: {e}")
            return "Report generated but email failed."