from __future__ import annotations

from pathlib import Path
import sys
from datetime import datetime

import pandas as pd

try:
    # When run as a module: python -m pipeline.main_pipeline
    from .loader import OpenFlightsLoader, load_raw_openflights
    from .cleaner_airports import AirportsCleaner, clean_airports
    from .cleaner_airlines import AirlinesCleaner, clean_airlines
    from .cleaner_routes import RoutesCleaner, clean_routes
except ImportError:  # Fallback when executed as a script: python pipeline/main_pipeline.py
    # Ensure project root is on sys.path so absolute package import works
    _ROOT = Path(__file__).resolve().parent.parent
    if str(_ROOT) not in sys.path:
        sys.path.insert(0, str(_ROOT))
    from pipeline.loader import OpenFlightsLoader, load_raw_openflights
    from pipeline.cleaner_airports import AirportsCleaner, clean_airports
    from pipeline.cleaner_airlines import AirlinesCleaner, clean_airlines
    from pipeline.cleaner_routes import RoutesCleaner, clean_routes


class FlightRoutePipeline:
    def __init__(self, base_dir: str | Path = ".", prefer_local: bool = True) -> None:
        self.base_path = Path(base_dir)
        self.prefer_local = prefer_local
        self.cleaned_dir = self.base_path / "cleaned_dataset"
        self.cleaned_dir.mkdir(parents=True, exist_ok=True)

        self.loader = OpenFlightsLoader(base_dir=self.base_path, prefer_local=self.prefer_local)
        self.airports_cleaner = AirportsCleaner()
        self.airlines_cleaner = AirlinesCleaner()
        self.routes_cleaner = RoutesCleaner()

    def run(self) -> dict[str, pd.DataFrame]:
        airports_df, airlines_df, routes_df = self.loader.load()

        airports_cleaned = self.airports_cleaner.clean(airports_df)
        airlines_cleaned = self.airlines_cleaner.clean(airlines_df)
        routes_cleaned = self.routes_cleaner.clean(
            routes_df, airlines_cleaned=airlines_cleaned, airports_cleaned=airports_cleaned
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        airports_cleaned.to_csv(self.cleaned_dir / f"airports_cleaned_pipeline.csv", index=False, encoding="utf-8")
        airlines_cleaned.to_csv(self.cleaned_dir / f"airlines_cleaned_pipeline.csv", index=False, encoding="utf-8")
        routes_cleaned.to_csv(self.cleaned_dir / f"routes_cleaned_pipeline.csv", index=False, encoding="utf-8")

        return {
            "airports_cleaned": airports_cleaned,
            "airlines_cleaned": airlines_cleaned,
            "routes_cleaned": routes_cleaned,
        }


def run_pipeline(base_dir: str | Path = ".", prefer_local: bool = True) -> dict[str, pd.DataFrame]:
    return FlightRoutePipeline(base_dir=base_dir, prefer_local=prefer_local).run()


if __name__ == "__main__":
    frames = run_pipeline()
    print("- airports_cleaned_pipeline*.csv")
    print("- airlines_cleaned_pipeline*.csv")
    print("- routes_cleaned_pipeline*.csv")
    print(f"Airports: {len(frames['airports_cleaned'])} rows")
    print(f"Airlines: {len(frames['airlines_cleaned'])} rows")
    print(f"Routes: {len(frames['routes_cleaned'])} rows")


