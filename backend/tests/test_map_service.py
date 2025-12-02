import os
from pathlib import Path

import pytest

import map_service

# Test create_map returns None when geocoding fails
def test_create_map_returns_none_when_geocode_fails(monkeypatch):
    monkeypatch.setattr(map_service, "geocoder", type("G", (), {"ip": lambda _: type("O", (), {"latlng": None})()}))
    result = map_service.create_map()
    assert result is None

# Test create_map handles successful geocoding and map saving
def test_create_map_handles_success(tmp_path, monkeypatch):
    fake_path = tmp_path / "public"
    fake_path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(map_service, "MAP_FILENAME", "test_map.html")

    class FakeGeo:
        latlng = [51.1, 17.0]

    def fake_save(m):
        return "/test_map.html?t=123"

    monkeypatch.setattr(map_service, "geocoder", type("G", (), {"ip": lambda _: FakeGeo()}))
    monkeypatch.setattr(map_service, "_save_map", lambda m: "/test_map.html?t=123")

    result = map_service.create_map()
    assert result["source"] == "ip"
    assert result["latlng"] == FakeGeo.latlng

