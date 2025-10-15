from __future__ import annotations

import pandas as pd


class RoutesCleaner:
    def clean(
        self,
        routes_df: pd.DataFrame,
        airlines_cleaned: pd.DataFrame,
        airports_cleaned: pd.DataFrame,
    ) -> pd.DataFrame:
        routes_cleaned = routes_df.copy()

        routes_cleaned = routes_cleaned.replace({
            "\\N": pd.NA,
            "nan": pd.NA,
            "NaN": pd.NA,
            "": pd.NA,
            "Unknown": pd.NA,
            "unknown": pd.NA,
            "-": pd.NA,
        })

        routes_cleaned["airline_id"] = pd.to_numeric(routes_cleaned["airline_id"], errors="coerce")
        routes_cleaned = routes_cleaned[routes_cleaned["airline_id"] > 0]

        routes_cleaned["source_airport_id"] = pd.to_numeric(routes_cleaned["source_airport_id"], errors="coerce")
        routes_cleaned["destination_airport_id"] = pd.to_numeric(routes_cleaned["destination_airport_id"], errors="coerce")

        routes_cleaned = routes_cleaned.dropna(subset=["source_airport", "destination_airport"])  # type: ignore[arg-type]
        routes_cleaned = routes_cleaned.dropna(subset=["source_airport_id", "destination_airport_id"])  # type: ignore[arg-type]

        routes_cleaned["stops"] = pd.to_numeric(routes_cleaned["stops"], errors="coerce").fillna(0)
        routes_cleaned["codeshare"] = routes_cleaned["codeshare"].fillna("N")
        routes_cleaned["equipment"] = routes_cleaned["equipment"].fillna("Unknown")

        routes_cleaned = routes_cleaned[
            routes_cleaned["source_airport"] != routes_cleaned["destination_airport"]
        ]

        routes_cleaned = routes_cleaned.drop_duplicates(
            subset=["airline_id", "source_airport_id", "destination_airport_id"], keep="first"
        )

        valid_airline_ids = set(airlines_cleaned["airline_id"].dropna())
        valid_airport_ids = set(airports_cleaned["airport_id"].dropna())
        routes_cleaned = routes_cleaned[routes_cleaned["airline_id"].isin(valid_airline_ids)]
        routes_cleaned = routes_cleaned[routes_cleaned["source_airport_id"].isin(valid_airport_ids)]
        routes_cleaned = routes_cleaned[routes_cleaned["destination_airport_id"].isin(valid_airport_ids)]

        string_columns = ["airline", "source_airport", "destination_airport", "codeshare", "equipment"]
        for col in string_columns:
            if col in routes_cleaned.columns:
                routes_cleaned[col] = routes_cleaned[col].astype(str).str.strip()
                routes_cleaned[col] = routes_cleaned[col].replace("nan", pd.NA)

        return routes_cleaned


def clean_routes(
    routes_df: pd.DataFrame,
    airlines_cleaned: pd.DataFrame,
    airports_cleaned: pd.DataFrame,
) -> pd.DataFrame:
    return RoutesCleaner().clean(routes_df, airlines_cleaned=airlines_cleaned, airports_cleaned=airports_cleaned)


