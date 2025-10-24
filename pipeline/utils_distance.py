from __future__ import annotations

import math
from typing import Tuple

import pandas as pd


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth.
    
    Args:
        lat1, lon1: Latitude and longitude of first point in decimal degrees
        lat2, lon2: Latitude and longitude of second point in decimal degrees
    
    Returns:
        Distance in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    return c * r


def calculate_route_distances(routes_df: pd.DataFrame, airports_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate distances for all routes using airport coordinates.
    
    Args:
        routes_df: DataFrame with route information
        airports_df: DataFrame with airport coordinates
    
    Returns:
        DataFrame with added distance_km column
    """
    # Create lookup dictionaries for coordinates
    airport_coords = {}
    for _, row in airports_df.iterrows():
        airport_coords[row['airport_id']] = (row['latitude'], row['longitude'])
    
    # Calculate distances
    distances = []
    for _, route in routes_df.iterrows():
        source_id = route['source_airport_id']
        dest_id = route['destination_airport_id']
        
        if source_id in airport_coords and dest_id in airport_coords:
            lat1, lon1 = airport_coords[source_id]
            lat2, lon2 = airport_coords[dest_id]
            distance = haversine_distance(lat1, lon1, lat2, lon2)
            distances.append(distance)
        else:
            distances.append(None)  # Missing coordinate data
    
    routes_with_distance = routes_df.copy()
    routes_with_distance['distance_km'] = distances
    
    return routes_with_distance


def get_airport_coordinates(airport_id: int, airports_df: pd.DataFrame) -> Tuple[float, float] | None:
    """
    Get coordinates for a specific airport.
    
    Args:
        airport_id: Airport ID to look up
        airports_df: DataFrame with airport information
    
    Returns:
        Tuple of (latitude, longitude) or None if not found
    """
    airport = airports_df[airports_df['airport_id'] == airport_id]
    if len(airport) > 0:
        return (airport.iloc[0]['latitude'], airport.iloc[0]['longitude'])
    return None
