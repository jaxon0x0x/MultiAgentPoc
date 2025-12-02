from dataclasses import dataclass
from contextlib import contextmanager
import sqlite3
from typing import List


@dataclass
class EmergencyService:
    service_type: str
    city: str
    email: str


class DatabaseDriver:
    def __init__(self, db_path: str = "sos.sqlite"):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS emergency_services")
            cursor.execute(
                """
                CREATE TABLE emergency_services (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_type TEXT NOT NULL,
                    city TEXT NOT NULL,
                    email TEXT NOT NULL
                )
                """
            )
            self._seed_services(cursor)
            conn.commit()

    def _seed_services(self, cursor) -> None:
        cursor.execute("SELECT COUNT(1) FROM emergency_services")
        if cursor.fetchone()[0] > 0:
            return

        cities = [
            "Warsaw",
            "Krakow",
            "Lodz",
            "Wroclaw",
            "Poznan",
            "Gdansk",
            "Szczecin",
            "Lublin",
            "Katowice",
            "Bialystok",
        ]
        services = []
        for city in cities:
            if city == "Bialystok":
                email = "wierzbowiczjan@gmail.com"
                services.extend([
                    ("hospital", city, email),
                    ("firestation", city, email),
                    ("policestation", city, email),
                ])
                continue
            services.append(("hospital", city, f"hospital@{city.lower()}.gov.pl"))
            services.append(("firestation", city, f"firestation@{city.lower()}.gov.pl"))
            services.append(("policestation", city, f"police@{city.lower()}.gov.pl"))

        cursor.executemany(
            "INSERT INTO emergency_services (service_type, city, email) VALUES (?, ?, ?)",
            services,
        )

    def list_services(self) -> List[EmergencyService]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT service_type, city, email FROM emergency_services")
            rows = cursor.fetchall()
            return [EmergencyService(*row) for row in rows]

    def get_services_by_city(self, city: str) -> List[EmergencyService]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT service_type, city, email FROM emergency_services WHERE city = ?",
                (city,),
            )
            rows = cursor.fetchall()
            return [EmergencyService(*row) for row in rows]

    def add_service(self, service: EmergencyService) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO emergency_services (service_type, city, email) VALUES (?, ?, ?)",
                (service.service_type, service.city, service.email),
            )
            conn.commit()

    def get_service_email(self, service_type: str, city: str | None = None) -> str | None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT email FROM emergency_services WHERE service_type = ?"
            params = [service_type]
            if city:
                query += " AND LOWER(city) = ?"
                params.append(city.lower())
            cursor.execute(query, tuple(params))
            row = cursor.fetchone()
            if row:
                return row[0]
            cursor.execute("SELECT email FROM emergency_services WHERE service_type = ? LIMIT 1", (service_type,))
            row = cursor.fetchone()
            return row[0] if row else None
