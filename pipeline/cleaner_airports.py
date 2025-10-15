from __future__ import annotations

import pandas as pd


class AirportsCleaner:
    def clean(self, airports_df: pd.DataFrame) -> pd.DataFrame:
        airports_cleaned = airports_df.copy()

        airports_cleaned = airports_cleaned.replace({
            "\\N": pd.NA,
            "nan": pd.NA,
            "NaN": pd.NA,
            "": pd.NA,
            "Unknown": pd.NA,
            "unknown": pd.NA,
        })

        airports_cleaned["iata"] = airports_cleaned["iata"].replace(["-", "nan", "NaN"], pd.NA)
        airports_cleaned["icao"] = airports_cleaned["icao"].replace(["-", "nan", "NaN"], pd.NA)

        airports_cleaned = airports_cleaned.dropna(subset=["latitude", "longitude"])
        airports_cleaned = airports_cleaned[
            (airports_cleaned["latitude"] >= -90)
            & (airports_cleaned["latitude"] <= 90)
            & (airports_cleaned["longitude"] >= -180)
            & (airports_cleaned["longitude"] <= 180)
        ]

        airports_cleaned["altitude"] = pd.to_numeric(airports_cleaned["altitude"], errors="coerce").fillna(0)
        airports_cleaned["timezone"] = pd.to_numeric(airports_cleaned["timezone"], errors="coerce")
        dst_mapping = {"E": "E", "A": "A", "S": "S", "O": "O", "Z": "Z", "N": "N", "U": "U"}
        airports_cleaned["dst"] = airports_cleaned["dst"].map(dst_mapping).fillna("U")
        airports_cleaned["type"] = airports_cleaned["type"].fillna("airport")
        airports_cleaned["source"] = airports_cleaned["source"].fillna("Unknown")
        airports_cleaned = airports_cleaned.drop_duplicates(subset=["airport_id"], keep="first")

        string_columns = [
            "name",
            "city",
            "country",
            "iata",
            "icao",
            "tz_database_time_zone",
            "type",
            "source",
        ]
        for col in string_columns:
            if col in airports_cleaned.columns:
                airports_cleaned[col] = airports_cleaned[col].astype(str).str.strip()
                airports_cleaned[col] = airports_cleaned[col].replace("nan", pd.NA)

        return airports_cleaned


def clean_airports(airports_df: pd.DataFrame) -> pd.DataFrame:
    return AirportsCleaner().clean(airports_df)


