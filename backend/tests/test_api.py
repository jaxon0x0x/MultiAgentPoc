import pytest

from db_driver import DatabaseDriver
import api

#testing if service normalization works correctly
def test_normalize_service_matches_known_types():
    assert api._normalize_service("Need ambulance urgently") == "hospital"
    assert api._normalize_service("There is a fire nearby") == "firestation"
    assert api._normalize_service("Police please") == "policestation"
    assert api._normalize_service("Something else") is None

#testing if email retrieval works with exact city match
def test_get_email_for_service_uses_exact_city(tmp_path, monkeypatch):
    driver = DatabaseDriver(str(tmp_path / "exact.sqlite"))

    # Pre-populate the database with test data
    monkeypatch.setattr(api, "DB", driver)

    email = api._get_email_for_service("fire", "Krakow")
    assert email == "firestation@krakow.gov.pl"

#testing if email retrieval works if unknown city and service
def test_get_email_for_service_returns_none_for_unknown(monkeypatch, tmp_path):
    driver = DatabaseDriver(str(tmp_path / "unknown.sqlite"))
    monkeypatch.setattr(api, "DB", driver)

    assert api._get_email_for_service("unicorn", "Warsaw") is None

#testing if sending incident note handles missing email correctly
@pytest.mark.asyncio
async def test_send_incident_note_reports_missing_email(monkeypatch):
    monkeypatch.setattr(api, "_get_email_for_service", lambda *args, **kwargs: None)
    monkeypatch.setattr(api, "_send_email_sync", lambda *args, **kwargs: None)

    assistant = api.AssistantFnc()
    result = await assistant.send_incident_note(
        incident_type="Fire",
        city="Warsaw",
        location="Main Street",
        casualties="None",
        details="Test details",
        recommended_service="fire",
        coordinates="52.2297,21.0122",
        photo_summary="",
    )

    assert "No email found" in result
