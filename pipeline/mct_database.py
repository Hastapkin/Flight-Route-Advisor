"""
Minimum Connection Time (MCT) Database
Contains MCT data for major airports to improve transit delay accuracy
"""

from typing import Dict, Optional, Tuple

# MCT database: airport_iata -> (domestic_mct_hours, international_mct_hours)
# MCT values in hours (converted from minutes)
# Based on IATA MCT standards and airport-specific data
MCT_DATABASE: Dict[str, Tuple[float, float]] = {
    # Major hubs - typically have efficient transfer facilities
    "DXB": (1.0, 1.5),  # Dubai - excellent transfer facilities
    "IST": (1.0, 1.5),  # Istanbul
    "SIN": (0.75, 1.25),  # Singapore - very efficient
    "HKG": (0.75, 1.25),  # Hong Kong
    "NRT": (1.0, 1.5),  # Tokyo Narita
    "ICN": (1.0, 1.5),  # Seoul Incheon
    "AMS": (0.75, 1.25),  # Amsterdam - efficient
    "FRA": (1.0, 1.5),  # Frankfurt
    "LHR": (1.5, 2.0),  # London Heathrow - can be slow
    "CDG": (1.5, 2.0),  # Paris - can be slow
    "JFK": (1.5, 2.5),  # New York JFK - can be very slow
    "LAX": (1.5, 2.5),  # Los Angeles
    "MIA": (1.5, 2.0),  # Miami
    "ATL": (1.0, 1.5),  # Atlanta - efficient domestic hub
    "DFW": (1.0, 1.5),  # Dallas/Fort Worth
    "ORD": (1.5, 2.0),  # Chicago O'Hare
    "DOH": (1.0, 1.5),  # Doha
    "AUH": (1.0, 1.5),  # Abu Dhabi
    "BKK": (1.0, 1.5),  # Bangkok
    "KUL": (1.0, 1.5),  # Kuala Lumpur
    "DME": (1.5, 2.0),  # Moscow Domodedovo
    "SVO": (1.5, 2.0),  # Moscow Sheremetyevo
    "PEK": (1.5, 2.0),  # Beijing
    "PVG": (1.5, 2.0),  # Shanghai Pudong
    "CAN": (1.0, 1.5),  # Guangzhou
    "SYD": (1.5, 2.0),  # Sydney
    "MEL": (1.5, 2.0),  # Melbourne
    "YYZ": (1.5, 2.0),  # Toronto
    "YVR": (1.5, 2.0),  # Vancouver
    "GRU": (1.5, 2.0),  # São Paulo
    "EZE": (1.5, 2.0),  # Buenos Aires
    "JNB": (1.5, 2.0),  # Johannesburg
    "CAI": (1.5, 2.0),  # Cairo
    "DXB": (1.0, 1.5),  # Dubai (duplicate but kept for clarity)
}

# Default MCT values (fallback)
DEFAULT_DOMESTIC_MCT = 1.0  # 1 hour for domestic transfers
DEFAULT_INTERNATIONAL_MCT = 1.5  # 1.5 hours for international transfers

# Additional buffer for terminal changes (in hours)
TERMINAL_CHANGE_BUFFER = 0.5  # 30 minutes additional time if terminal change required


def get_mct(
    airport_iata: str, 
    is_international: bool = True,
    has_terminal_change: bool = False
) -> float:
    """
    Get Minimum Connection Time (MCT) for an airport
    
    Args:
        airport_iata: Airport IATA code
        is_international: True if international transfer, False for domestic
        has_terminal_change: True if terminal change is required
        
    Returns:
        MCT in hours
    """
    # Look up in database
    if airport_iata in MCT_DATABASE:
        domestic_mct, international_mct = MCT_DATABASE[airport_iata]
        base_mct = international_mct if is_international else domestic_mct
    else:
        # Use defaults
        base_mct = DEFAULT_INTERNATIONAL_MCT if is_international else DEFAULT_DOMESTIC_MCT
    
    # Add buffer for terminal changes
    if has_terminal_change:
        base_mct += TERMINAL_CHANGE_BUFFER
    
    return base_mct


def is_international_transfer(
    source_country: str, 
    dest_country: str, 
    transit_country: str
) -> bool:
    """
    Determine if a transfer is international
    
    Args:
        source_country: Source country
        dest_country: Destination country
        transit_country: Transit country
        
    Returns:
        True if transfer involves crossing borders
    """
    # Transfer is international if transit country differs from source or destination
    return (transit_country != source_country) or (transit_country != dest_country)

