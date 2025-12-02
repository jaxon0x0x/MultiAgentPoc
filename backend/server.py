import os
import json
import base64
import logging
import uuid
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from livekit import api
from openai import OpenAI
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from map_service import create_map

load_dotenv()
app = Flask(__name__)

# Enable CORS that frontend can access the API from different oport
CORS(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
logger = logging.getLogger("server")

# Analyze image using OpenAI's GPT-4o-mini model in base 64 format
def _analyze_image(path: str) -> str:
    try:
        with open(path, "rb") as f:
            image_bytes = f.read()
            b64 = base64.b64encode(image_bytes).decode("ascii")

        res = client.chat.completions.create(
            model="gpt-4o-mini",  # Use gpt-4o for better image recognition
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an experienced 112 emergency dispatcher. "
                        "Your task is to assess the situation based on the photo. "
                        "Be specific, factual, and rely ONLY on what you can see."
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Analyze this photo and create a report in the following structure:\n\n"
                                "1. TYPE OF INCIDENT: (e.g., Traffic accident, Fire, Assault)\n"
                                "2. DETAILS OF VEHICLES/OBJECTS: (Make, color, type of damage)\n"
                                "3. CASUALTIES: (Number, condition, position. If none visible, write: 'NO VISIBLE CASUALTIES')\n"
                                "4. FIRE/SMOKE: (If none visible, write: 'NO VISIBLE FIRE')\n"
                                "5. ENVIRONMENTAL HAZARDS: (e.g., fluid leaks, blocked road, glass, downed wires)\n\n"
                                "Assess the situation briefly and professionally."
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=400
        )
        return res.choices[0].message.content
    except Exception as e:
        logger.error("Analysis failed", exc_info=e)
        return "Analysis unavailable."

# Endpoint to generate LiveKit access token and return jwt token
@app.route("/getToken")
async def get_token():
    room = request.args.get("room", f"room-{uuid.uuid4().hex[:8]}")
    name = request.args.get("name", "User")
    token = api.AccessToken(os.getenv("LIVEKIT_API_KEY"), os.getenv("LIVEKIT_API_SECRET")) \
        .with_identity(name).with_name(name).with_grants(api.VideoGrants(room_join=True, room=room))
    return token.to_jwt()

# Endpoint to upload photo and analyze it
@app.route("/upload-photo", methods=["POST"])
def upload_photo():
    if "photo" not in request.files: return jsonify({"error": "No file"}), 400
    f = request.files["photo"]
    fname = f"{uuid.uuid4().hex}_{secure_filename(f.filename)}"
    path = os.path.join(UPLOAD_FOLDER, fname)
    f.save(path)

    analysis = _analyze_image(path)
    with open(path + ".analysis.txt", "w", encoding="utf-8") as txt:
        txt.write(analysis)

    return jsonify({"url": f"{request.url_root}uploads/{fname}", "analysis": analysis})

# Static endpoint to serve uploaded files to frontend
@app.route("/uploads/<path:filename>")
def serve_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route("/data", methods=["POST"])
async def publish_data():
    data = request.get_json()
    url = data.get("url")
    analysis = data.get("analysis", "")

    # Recovery: Read from file if missing
    if not analysis and url:
        try:
            fname = url.split("/")[-1]
            txt_path = os.path.join(UPLOAD_FOLDER, fname + ".analysis.txt")
            if os.path.exists(txt_path):
                with open(txt_path, "r", encoding="utf-8") as f: analysis = f.read()
        except:
            pass

    async with api.LiveKitAPI(os.getenv("LIVEKIT_URL"), os.getenv("LIVEKIT_API_KEY"),
                              os.getenv("LIVEKIT_API_SECRET")) as lk_api:
        rooms = (await lk_api.room.list_rooms(api.ListRoomsRequest())).rooms
        if not rooms: return jsonify({"error": "No rooms"}), 400

        payload = json.dumps({"url": url, "analysis": analysis})
        await lk_api.room.send_data(api.SendDataRequest(
            room=rooms[0].name, data=payload.encode("utf-8"), topic=data.get("topic"), kind="RELIABLE"
        ))

    return jsonify({"status": "ok"})


@app.route("/map")
def map_view(): return jsonify(create_map() or {})

@app.route("/ping", methods=["GET"])
def help():
    return jsonify({"message": "Works!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)