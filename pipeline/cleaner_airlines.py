from __future__ import annotations

import pandas as pd


class AirlinesCleaner:
    def clean(self, airlines_df: pd.DataFrame) -> pd.DataFrame:
        airlines_cleaned = airlines_df.copy()

        airlines_cleaned = airlines_cleaned.replace({
            "\\N": pd.NA,
            "nan": pd.NA,
            "NaN": pd.NA,
            "": pd.NA,
            "Unknown": pd.NA,
            "unknown": pd.NA,
            "-": pd.NA,
        })

        airlines_cleaned["airline_id"] = pd.to_numeric(airlines_cleaned["airline_id"], errors="coerce")
        airlines_cleaned = airlines_cleaned[airlines_cleaned["airline_id"] > 0]

        airlines_cleaned["iata"] = airlines_cleaned["iata"].replace(["-", "nan", "NaN"], pd.NA)
        airlines_cleaned["icao"] = airlines_cleaned["icao"].replace(["-", "nan", "NaN"], pd.NA)

        airlines_cleaned = airlines_cleaned[~(airlines_cleaned["iata"].isna() & airlines_cleaned["icao"].isna())]

        airlines_cleaned["callsign"] = airlines_cleaned["callsign"].replace(["-", "nan", "NaN"], pd.NA)
        airlines_cleaned["active"] = airlines_cleaned["active"].replace(["\\N", "nan", "NaN"], "N").fillna("N")
        airlines_cleaned["country"] = airlines_cleaned["country"].fillna("Unknown")
        airlines_cleaned = airlines_cleaned.drop_duplicates(subset=["airline_id"], keep="first")

        string_columns = ["name", "alias", "iata", "icao", "callsign", "country"]
        for col in string_columns:
            if col in airlines_cleaned.columns:
                airlines_cleaned[col] = airlines_cleaned[col].astype(str).str.strip()
                airlines_cleaned[col] = airlines_cleaned[col].replace("nan", pd.NA)

        return airlines_cleaned


def clean_airlines(airlines_df: pd.DataFrame) -> pd.DataFrame:
    return AirlinesCleaner().clean(airlines_df)


