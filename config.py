"""
Configuration file for Flight Route Advisor
Centralized settings and constants
"""

from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
CLEANED_DIR = DATA_DIR / "cleaned"
GEPHI_DIR = DATA_DIR / "gephi"
RAW_DIR = DATA_DIR / "raw"

# Data URLs
OPENFLIGHTS_BASE_URL = "https://raw.githubusercontent.com/jpatokal/openflights/master/data"
AIRPORTS_URL = f"{OPENFLIGHTS_BASE_URL}/airports.dat"
AIRLINES_URL = f"{OPENFLIGHTS_BASE_URL}/airlines.dat"
ROUTES_URL = f"{OPENFLIGHTS_BASE_URL}/routes.dat"

# Data schemas
AIRPORT_COLUMNS = [
    "airport_id", "name", "city", "country", "iata", "icao",
    "latitude", "longitude", "altitude", "timezone", "dst",
    "tz_database_time_zone", "type", "source"
]

AIRLINE_COLUMNS = [
    "airline_id", "name", "alias", "iata", "icao", "callsign",
    "country", "active"
]

ROUTE_COLUMNS = [
    "airline", "airline_id", "source_airport", "source_airport_id",
    "destination_airport", "destination_airport_id", "codeshare",
    "stops", "equipment"
]

# Analysis settings
DEFAULT_TOP_HUBS = 10
MAX_ALTERNATIVE_PATHS = 5
EARTH_RADIUS_KM = 6371  # Mean radius of Earth

# Flight time calculation settings
AVERAGE_FLIGHT_SPEED_KMH = 800  # Average commercial aircraft speed in km/h (fallback)

# Distance-based speed profiles (more accurate than fixed speed)
FLIGHT_SPEED_PROFILES = {
    "short_haul": {
        "max_distance_km": 1000,
        "speed_kmh": 650,  # Slower due to climb/descent time
        "buffer_hours": 0.5  # Taxi, takeoff, landing
    },
    "medium_haul": {
        "max_distance_km": 5000,
        "speed_kmh": 825,  # Medium-haul cruise speed
        "buffer_hours": 0.75
    },
    "long_haul": {
        "max_distance_km": float('inf'),
        "speed_kmh": 925,  # Long-haul cruise speed
        "buffer_hours": 1.0
    }
}

TRANSIT_DELAY_HOURS = {
    "hub": 2.0,      # Large hub airports (high degree centrality)
    "medium": 1.5,   # Medium airports
    "small": 1.0     # Small airports
}

# Hub classification thresholds (based on degree centrality)
HUB_DEGREE_THRESHOLD = 0.01  # Top 1% are considered hubs
MEDIUM_DEGREE_THRESHOLD = 0.005  # Top 0.5% to 1% are medium

# Gephi export settings
GEPHI_EXPORT_SETTINGS = {
    "full_network": {
        "name": "flight_network_full.gexf",
        "description": "Complete flight network"
    },
    "major_hubs": {
        "name": "flight_network_major_hubs.gexf", 
        "description": "Top 20% hubs by degree centrality",
        "hub_percentage": 0.2
    },
    "long_distance": {
        "name": "flight_network_long_distance.gexf",
        "description": "Routes longer than 5000km",
        "min_distance_km": 5000
    },
    "international": {
        "name": "flight_network_international.gexf",
        "description": "Cross-border routes"
    },
    "country_level": {
        "name": "flight_network_country_level.gexf",
        "description": "Country-to-country connections"
    }
}

# Streamlit settings
STREAMLIT_CONFIG = {
    "page_title": "Flight Route Advisor",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# Hub removal impact thresholds
IMPACT_THRESHOLDS = {
    "CRITICAL": {
        "connectivity_broken": True,
        "description": "Network connectivity is broken"
    },
    "HIGH": {
        "components_increase": 5,
        "description": "Significant increase in disconnected components"
    },
    "MEDIUM": {
        "edges_lost": 100,
        "description": "Moderate number of routes lost"
    },
    "LOW": {
        "description": "Minimal impact on network"
    }
}
