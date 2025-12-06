"""
Airline Alliance Database
Contains information about airline alliances and codeshare agreements
"""

from typing import Dict, Set, Optional, List

# Major airline alliances
ALLIANCES: Dict[str, Set[str]] = {
    "Star Alliance": {
        "UA", "LH", "AC", "NH", "TG", "SQ", "OZ", "CA", "LO", "OS", "SK", 
        "LX", "TP", "SA", "NZ", "EK", "AI", "MS", "ET", "BR", "CM", "AV"
    },
    "OneWorld": {
        "AA", "BA", "IB", "AY", "CX", "QF", "JL", "RJ", "LA", "AS", "MH", 
        "QR", "UL", "S7", "FJ", "MX"
    },
    "SkyTeam": {
        "DL", "AF", "KL", "AM", "CZ", "KE", "VS", "AZ", "SU", "RO", "OK", 
        "GA", "MU", "CI", "MF", "VN", "AR", "UX", "KM"
    }
}

# Reverse mapping: airline -> alliance
AIRLINE_TO_ALLIANCE: Dict[str, str] = {}
for alliance, airlines in ALLIANCES.items():
    for airline in airlines:
        AIRLINE_TO_ALLIANCE[airline.upper()] = alliance

# Codeshare indicators (from OpenFlights data)
CODESHARE_INDICATORS = {"Y", "y", "1", "true", "yes"}


def get_alliance(airline_code: str) -> Optional[str]:
    """
    Get alliance for an airline
    
    Args:
        airline_code: Airline IATA code
        
    Returns:
        Alliance name or None if not in any alliance
    """
    return AIRLINE_TO_ALLIANCE.get(airline_code.upper())


def is_same_alliance(airline1: str, airline2: str) -> bool:
    """
    Check if two airlines are in the same alliance
    
    Args:
        airline1: First airline IATA code
        airline2: Second airline IATA code
        
    Returns:
        True if same alliance
    """
    alliance1 = get_alliance(airline1)
    alliance2 = get_alliance(airline2)
    
    if not alliance1 or not alliance2:
        return False
    
    return alliance1 == alliance2


def validate_codeshare_route(
    airline1: str,
    airline2: str,
    codeshare_flag: Optional[str] = None
) -> bool:
    """
    Validate if a codeshare route is valid
    
    Args:
        airline1: First airline IATA code
        airline2: Second airline IATA code
        codeshare_flag: Codeshare flag from route data
        
    Returns:
        True if valid codeshare route
    """
    # If codeshare flag is set, it's a codeshare route
    if codeshare_flag and codeshare_flag.upper() in CODESHARE_INDICATORS:
        return True
    
    # Check if same alliance (alliance partners can codeshare)
    if is_same_alliance(airline1, airline2):
        return True
    
    # Same airline (not codeshare, but valid)
    if airline1.upper() == airline2.upper():
        return True
    
    return False


def get_alliance_airlines(alliance_name: str) -> Set[str]:
    """
    Get all airlines in an alliance
    
    Args:
        alliance_name: Alliance name
        
    Returns:
        Set of airline IATA codes
    """
    return ALLIANCES.get(alliance_name, set())


def filter_by_alliance(
    airlines: List[str],
    alliance_name: Optional[str] = None
) -> List[str]:
    """
    Filter airlines by alliance
    
    Args:
        airlines: List of airline codes
        alliance_name: Alliance name to filter by (None for all)
        
    Returns:
        Filtered list of airline codes
    """
    if not alliance_name:
        return airlines
    
    alliance_airlines = get_alliance_airlines(alliance_name)
    return [a for a in airlines if a.upper() in alliance_airlines]

