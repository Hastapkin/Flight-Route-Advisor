"""
Input validation and error handling utilities for Flight Route Advisor
"""

from typing import Dict, List, Optional, Any, Tuple
import re


class ValidationError(Exception):
    """Custom exception for validation errors"""
    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


def validate_iata_code(iata: str) -> Tuple[bool, Optional[str]]:
    """
    Validate IATA airport code format
    
    Args:
        iata: IATA code to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not iata:
        return False, "IATA code cannot be empty"
    
    if not isinstance(iata, str):
        return False, "IATA code must be a string"
    
    iata = iata.strip().upper()
    
    # IATA codes are 3 uppercase letters
    if not re.match(r'^[A-Z]{3}$', iata):
        return False, f"IATA code '{iata}' must be exactly 3 uppercase letters"
    
    return True, None


def validate_airport_codes(source_iata: str, dest_iata: str) -> Tuple[bool, Optional[str]]:
    """
    Validate source and destination airport codes
    
    Args:
        source_iata: Source airport IATA code
        dest_iata: Destination airport IATA code
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate source
    is_valid, error = validate_iata_code(source_iata)
    if not is_valid:
        return False, f"Source airport: {error}"
    
    # Validate destination
    is_valid, error = validate_iata_code(dest_iata)
    if not is_valid:
        return False, f"Destination airport: {error}"
    
    # Check if same
    if source_iata.strip().upper() == dest_iata.strip().upper():
        return False, "Source and destination airports cannot be the same"
    
    return True, None


def validate_objective(objective: str) -> Tuple[bool, Optional[str]]:
    """
    Validate optimization objective
    
    Args:
        objective: Optimization objective string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_objectives = ["distance", "transfers", "fastest", "popular"]
    
    if objective not in valid_objectives:
        return False, f"Objective must be one of: {', '.join(valid_objectives)}"
    
    return True, None


def validate_max_stops(max_stops: Optional[int]) -> Tuple[bool, Optional[str]]:
    """
    Validate maximum stops parameter
    
    Args:
        max_stops: Maximum number of stops (None for unlimited)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if max_stops is None:
        return True, None
    
    if not isinstance(max_stops, int):
        return False, "max_stops must be an integer or None"
    
    if max_stops < 0:
        return False, "max_stops cannot be negative"
    
    if max_stops > 10:
        return False, "max_stops cannot exceed 10 (performance limit)"
    
    return True, None


def validate_preferences(preferences: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate user preferences
    
    Args:
        preferences: Dictionary of preferences
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(preferences, dict):
        return False, "Preferences must be a dictionary"
    
    # Validate avoid_countries
    if "avoid_countries" in preferences:
        avoid = preferences["avoid_countries"]
        if not isinstance(avoid, list):
            return False, "avoid_countries must be a list"
        for country in avoid:
            if not isinstance(country, str) or not country.strip():
                return False, "All countries in avoid_countries must be non-empty strings"
    
    # Validate allowed_countries
    if "allowed_countries" in preferences:
        allowed = preferences["allowed_countries"]
        if not isinstance(allowed, list):
            return False, "allowed_countries must be a list"
        for country in allowed:
            if not isinstance(country, str) or not country.strip():
                return False, "All countries in allowed_countries must be non-empty strings"
    
    # Validate preferred_airlines
    if "preferred_airlines" in preferences:
        airlines = preferences["preferred_airlines"]
        if not isinstance(airlines, list):
            return False, "preferred_airlines must be a list"
        for airline in airlines:
            if not isinstance(airline, str) or not airline.strip():
                return False, "All airlines in preferred_airlines must be non-empty strings"
    
    # Check for conflicting preferences
    if "avoid_countries" in preferences and "allowed_countries" in preferences:
        avoid = set(c.lower() for c in preferences["avoid_countries"])
        allowed = set(c.lower() for c in preferences["allowed_countries"])
        if avoid.intersection(allowed):
            return False, "avoid_countries and allowed_countries cannot overlap"
    
    return True, None


def validate_trip_type(trip_type: str) -> Tuple[bool, Optional[str]]:
    """
    Validate trip type
    
    Args:
        trip_type: Trip type string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_types = ["one_way", "round_trip"]
    
    if trip_type not in valid_types:
        return False, f"Trip type must be one of: {', '.join(valid_types)}"
    
    return True, None


def create_error_response(error_message: str, error_type: str = "validation_error") -> Dict[str, Any]:
    """
    Create standardized error response
    
    Args:
        error_message: Error message
        error_type: Type of error
        
    Returns:
        Error response dictionary
    """
    return {
        "error": error_message,
        "error_type": error_type,
        "success": False
    }


def create_success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create standardized success response
    
    Args:
        data: Response data
        
    Returns:
        Success response dictionary
    """
    return {
        **data,
        "success": True
    }


def validate_route_request(
    source_iata: str,
    dest_iata: str,
    objective: str = "distance",
    preferences: Optional[Dict[str, Any]] = None,
    trip_type: str = "one_way",
    max_stops: Optional[int] = None
) -> Tuple[bool, Optional[str]]:
    """
    Comprehensive validation for route finding request
    
    Args:
        source_iata: Source airport IATA code
        dest_iata: Destination airport IATA code
        objective: Optimization objective
        preferences: User preferences
        trip_type: Trip type
        max_stops: Maximum stops
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate airport codes
    is_valid, error = validate_airport_codes(source_iata, dest_iata)
    if not is_valid:
        return False, error
    
    # Validate objective
    is_valid, error = validate_objective(objective)
    if not is_valid:
        return False, error
    
    # Validate trip type
    is_valid, error = validate_trip_type(trip_type)
    if not is_valid:
        return False, error
    
    # Validate max stops
    is_valid, error = validate_max_stops(max_stops)
    if not is_valid:
        return False, error
    
    # Validate preferences
    if preferences:
        is_valid, error = validate_preferences(preferences)
        if not is_valid:
            return False, error
    
    return True, None

