"""
Utility to estimate flight time from distance.
Uses average commercial aircraft speed (850 km/h) for all passenger flights.
Transit times are randomly generated between 2-5 hours.
Can be run as a script to add flight_time columns to routes_graph.csv.
Supports both single-leg routes and multi-leg routes with transit.
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

# Average speed for commercial passenger aircraft (km/h)
AVERAGE_AIRCRAFT_SPEED_KMH = 850.0

# Transit time range (hours)
# Randomly selected between 2-5 hours for each transit
TRANSIT_TIME_MIN_HOURS = 2.0
TRANSIT_TIME_MAX_HOURS = 5.0


def compute_flight_time(distance_km: float) -> Optional[float]:
    """
    Estimate flight time (hours) for a single leg using average commercial aircraft speed.
    
    Args:
        distance_km: Distance in kilometers for one flight leg
        
    Returns:
        Flight time in hours (float) or None if distance is invalid
    """
    if distance_km is None or pd.isna(distance_km) or distance_km <= 0:
        return None

    # Simple calculation: distance / speed
    return distance_km / AVERAGE_AIRCRAFT_SPEED_KMH


def compute_total_route_time(
    legs: List[Dict[str, Any]], 
    use_random_transit: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Calculate total flight time for a route with multiple legs (transit).
    Transit times are randomly generated between 2-5 hours for each transit stop.
    
    Args:
        legs: List of leg dictionaries, each containing 'distance_km'
              Example: [{'distance_km': 1000}, {'distance_km': 2000}]
        use_random_transit: If True, randomly generate transit time (2-5h) for each stop.
                           If False, use average transit time (3.5h).
        
    Returns:
        Dictionary with:
        - 'total_flight_time_hours': Sum of all leg flight times
        - 'total_transit_time_hours': Sum of transit times (random 2-5h per transit)
        - 'total_route_time_hours': Total time including flight + transit
        - 'leg_times': List of flight times for each leg
        - 'transit_times': List of transit times for each transit stop (hours)
        - 'number_of_transits': Number of transit stops
        Or None if legs are invalid
    """
    if not legs or len(legs) == 0:
        return None
    
    leg_times = []
    total_flight_time = 0.0
    
    # Calculate flight time for each leg
    for leg in legs:
        distance = leg.get('distance_km', 0)
        if distance is None or pd.isna(distance) or distance <= 0:
            continue
        
        leg_time = compute_flight_time(distance)
        if leg_time is None:
            continue
        
        leg_times.append(leg_time)
        total_flight_time += leg_time
    
    if len(leg_times) == 0:
        return None
    
    # Number of transits = number of legs - 1
    # Example: A->B->C has 2 legs, 1 transit at B
    number_of_transits = len(legs) - 1
    
    # Generate transit times (random 2-5h for each transit)
    transit_times = []
    total_transit_time = 0.0
    
    if number_of_transits > 0:
        for _ in range(number_of_transits):
            if use_random_transit:
                transit_time = random.uniform(TRANSIT_TIME_MIN_HOURS, TRANSIT_TIME_MAX_HOURS)
            else:
                # Use average if not random
                transit_time = (TRANSIT_TIME_MIN_HOURS + TRANSIT_TIME_MAX_HOURS) / 2.0
            transit_times.append(transit_time)
            total_transit_time += transit_time
    
    total_route_time = total_flight_time + total_transit_time
    
    return {
        'total_flight_time_hours': total_flight_time,
        'total_transit_time_hours': total_transit_time,
        'total_route_time_hours': total_route_time,
        'leg_times': leg_times,
        'transit_times': transit_times,
        'number_of_transits': number_of_transits
    }


def add_flight_time_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add flight_time_hours and flight_time_minutes columns to a routes DataFrame."""
    df = df.copy()
    df["flight_time_hours"] = df["distance_km"].apply(compute_flight_time)
    df["flight_time_minutes"] = df["flight_time_hours"] * 60
    return df


def main(input_path: Path, output_path: Path) -> None:
    routes = pd.read_csv(input_path)
    if "distance_km" not in routes.columns:
        raise ValueError("Input file must contain distance_km column.")
    routes_with_time = add_flight_time_columns(routes)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    routes_with_time.to_csv(output_path, index=False, encoding="utf-8")
    print(f"Saved with flight times: {output_path} (rows: {len(routes_with_time)})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Add estimated flight_time columns to routes_graph.csv"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/cleaned/routes_graph.csv"),
        help="Input routes file with distance_km",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/cleaned/routes_with_time.csv"),
        help="Output file with flight_time columns",
    )
    args = parser.parse_args()
    main(args.input, args.output)

