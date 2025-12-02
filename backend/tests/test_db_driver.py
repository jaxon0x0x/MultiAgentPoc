import asyncio
from pathlib import Path

import pytest

from db_driver import DatabaseDriver, EmergencyService

# Test adding a service and listing it
def test_add_service_and_list(tmp_path):
    db_path = tmp_path / "test_services.sqlite"
    driver = DatabaseDriver(str(db_path))

    extra = EmergencyService("hospital", "Testville", "test@example.com")
    driver.add_service(extra)

    # Verify it appears in the list BECAUSE list_services returns all populated services
    matches = [svc for svc in driver.list_services() if svc.city == "Testville"]
    assert matches == [extra]

# Test retrieving service email by type and city
def test_get_services_by_city_returns_all(tmp_path):
    db_path = tmp_path / "cities.sqlite"
    driver = DatabaseDriver(str(db_path))

    warsaw = driver.get_services_by_city("Warsaw")
    assert len(warsaw) == 3
    assert {svc.service_type for svc in warsaw} == {"hospital", "firestation", "policestation"}
