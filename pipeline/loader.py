from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
import requests
from io import StringIO


AIRPORTS_URL = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat"
AIRLINES_URL = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airlines.dat"
ROUTES_URL = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/routes.dat"


def _fetch_csv(url: str) -> str:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.text


def _read_openflights_csv(text: str, columns: list[str]) -> pd.DataFrame:
    return pd.read_csv(StringIO(text), header=None, names=columns)


def _read_local_csv(path: Path, columns: list[str]) -> pd.DataFrame:
    return pd.read_csv(path, header=None, names=columns)


class OpenFlightsLoader:
    """Loader for OpenFlights datasets supporting local or remote sources."""

    def __init__(self, base_dir: Path | str = ".", prefer_local: bool = True) -> None:
        self.base = Path(base_dir)
        self.raw_dir = self.base / "raw_dataset"
        self.prefer_local = prefer_local

    def load(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        airport_columns = [
            "airport_id", "name", "city", "country", "iata", "icao",
            "latitude", "longitude", "altitude", "timezone", "dst",
            "tz_database_time_zone", "type", "source",
        ]

        airline_columns = [
            "airline_id", "name", "alias", "iata", "icao", "callsign",
            "country", "active",
        ]

        route_columns = [
            "airline", "airline_id", "source_airport", "source_airport_id",
            "destination_airport", "destination_airport_id", "codeshare",
            "stops", "equipment",
        ]

        airports_df: pd.DataFrame
        airlines_df: pd.DataFrame
        routes_df: pd.DataFrame

        if self.prefer_local and (self.raw_dir / "airports.csv").exists() and (self.raw_dir / "airlines.csv").exists() and (self.raw_dir / "routes.csv").exists():
            airports_df = _read_local_csv(self.raw_dir / "airports.csv", airport_columns)
            airlines_df = _read_local_csv(self.raw_dir / "airlines.csv", airline_columns)
            routes_df = _read_local_csv(self.raw_dir / "routes.csv", route_columns)
        else:
            airports_df = _read_openflights_csv(_fetch_csv(AIRPORTS_URL), airport_columns)
            airlines_df = _read_openflights_csv(_fetch_csv(AIRLINES_URL), airline_columns)
            routes_df = _read_openflights_csv(_fetch_csv(ROUTES_URL), route_columns)

        # Basic type coercions for numeric-like columns
        for col in ["airport_id", "altitude", "timezone"]:
            if col in airports_df.columns:
                airports_df[col] = pd.to_numeric(airports_df[col], errors="coerce")

        for col in ["latitude", "longitude"]:
            if col in airports_df.columns:
                airports_df[col] = pd.to_numeric(airports_df[col], errors="coerce")

        if "airline_id" in airlines_df.columns:
            airlines_df["airline_id"] = pd.to_numeric(airlines_df["airline_id"], errors="coerce")

        if "stops" in routes_df.columns:
            routes_df["stops"] = pd.to_numeric(routes_df["stops"], errors="coerce")

        return airports_df, airlines_df, routes_df


def load_raw_openflights(prefer_local: bool = True, base_dir: Path | str = ".") -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    loader = OpenFlightsLoader(base_dir=base_dir, prefer_local=prefer_local)
    return loader.load()


