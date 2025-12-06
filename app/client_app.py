"""
Flight Route Advisor - Client-Side Application
Modern interface inspired by FlightConnections
"""

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from typing import Dict, List, Tuple, Any, Optional
import sys
from pathlib import Path
import math

# Add pipeline to path
sys.path.append(str(Path(__file__).parent.parent))

from pipeline.graph_analyzer import FlightGraphAnalyzer, create_flight_analyzer


# Helper functions
def get_airport_display_map(airports_df: pd.DataFrame) -> Dict[str, str]:
    """Return mapping from IATA to descriptive label."""
    display_map = {}
    for _, row in airports_df[airports_df['iata'].notna()].iterrows():
        iata = row['iata']
        if not iata:
            continue
        display_map[iata] = f"{iata} - {row.get('name', '')} ({row.get('city', '')}, {row.get('country', '')})"
    return display_map


def format_time_hours(hours: float) -> str:
    """Format time in hours to 'Xh Ym' format"""
    if hours < 0:
        return "0h 0m"
    h = int(hours)
    m = int((hours - h) * 60)
    return f"{h}h {m}m"


# Page configuration
st.set_page_config(
    page_title="Flight Route Advisor",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items=None
)

# Hide default Streamlit UI elements
hide_streamlit_style = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    div[data-testid="stToolbar"] {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Custom CSS - FlightConnections style
st.markdown("""
<style>
    /* Base styling */
    .stApp {
        background: #f5f5f5;
        color: #333333;
    }
    
    /* Top header */
    .top-header {
        background: #ffffff;
        border-bottom: 1px solid #e0e0e0;
        padding: 0.75rem 1.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .header-content {
        display: flex;
        align-items: center;
        justify-content: space-between;
        max-width: 100%;
    }
    
    .logo {
        font-size: 1.5rem;
        font-weight: 700;
        color: #2563eb;
    }
    
    .search-fields {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        flex: 1;
        max-width: 600px;
        margin: 0 2rem;
    }
    
    .search-field {
        flex: 1;
        padding: 0.5rem 1rem;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        font-size: 0.9rem;
    }
    
    /* Filter bar */
    .filter-bar {
        background: #ffffff;
        border-bottom: 1px solid #e0e0e0;
        padding: 0.75rem 1.5rem;
        display: flex;
        gap: 1rem;
        align-items: center;
        flex-wrap: wrap;
    }
    
    .filter-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.85rem;
        color: #6b7280;
    }
    
    /* Route info panel */
    .route-panel {
        background: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .route-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1f2937;
        margin-bottom: 0.75rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid #e5e7eb;
    }
    
    .route-metrics {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
        gap: 0.75rem;
        margin-top: 0.75rem;
    }
    
    .metric-box {
        background: #f9fafb;
        padding: 0.75rem;
        border-radius: 6px;
        border: 1px solid #e5e7eb;
    }
    
    .metric-label {
        font-size: 0.75rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.25rem;
    }
    
    .metric-value {
        font-size: 1.1rem;
        font-weight: 600;
        color: #111827;
    }
    
    .leg-item {
        background: #f9fafb;
        border-left: 3px solid #3b82f6;
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-radius: 4px;
        font-size: 0.9rem;
    }
    
    .leg-route {
        font-weight: 600;
        color: #1f2937;
        margin-bottom: 0.25rem;
    }
    
    .leg-details {
        color: #6b7280;
        font-size: 0.85rem;
    }
    
    /* Airport legend */
    .airport-legend {
        position: absolute;
        bottom: 20px;
        left: 20px;
        background: rgba(255, 255, 255, 0.95);
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        z-index: 1000;
        font-size: 0.85rem;
    }
    
    .legend-title {
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #1f2937;
    }
    
    .legend-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin: 0.25rem 0;
    }
    
    .legend-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
    }
    
    /* Route list */
    .route-list-item {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 6px;
        padding: 0.75rem;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .route-list-item:hover {
        border-color: #3b82f6;
        box-shadow: 0 2px 4px rgba(59, 130, 246, 0.1);
    }
    
    .route-list-item.selected {
        border-color: #3b82f6;
        background: #eff6ff;
    }
    
    /* Button styling */
    .stButton > button {
        background: #3b82f6;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        background: #2563eb;
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div {
        background: #ffffff;
        border: 1px solid #d1d5db;
        border-radius: 6px;
    }
    
    /* Text input styling */
    .stTextInput > div > div > input {
        background: #ffffff;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        color: #111827;
    }
    
    /* Radio button styling */
    .stRadio > div {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 6px;
        padding: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    """Load flight data with caching"""
    try:
        analyzer = create_flight_analyzer("data/cleaned")
        return analyzer
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None


def get_cache_key(source: str, dest: str, max_stops: Optional[int], max_routes: int) -> str:
    """Generate cache key for route search"""
    max_stops_str = str(max_stops) if max_stops is not None else "None"
    return f"routes_{source}_{dest}_{max_stops_str}_{max_routes}"


def find_routes_cached(
    analyzer: FlightGraphAnalyzer,
    source_iata: str,
    dest_iata: str,
    max_stops: Optional[int],
    max_routes: int
) -> List[Dict[str, Any]]:
    """
    Cached version of find_all_routes using session state for better performance
    """
    cache_key = get_cache_key(source_iata, dest_iata, max_stops, max_routes)
    
    # Check cache in session state
    if 'route_cache' not in st.session_state:
        st.session_state['route_cache'] = {}
    
    if cache_key in st.session_state['route_cache']:
        return st.session_state['route_cache'][cache_key]
    
    # Find routes
    routes = analyzer.find_all_routes(
        source_iata,
        dest_iata,
        preferences={},
        max_stops=max_stops,
        max_routes=max_routes
    )
    
    # Store in cache
    st.session_state['route_cache'][cache_key] = routes
    
    return routes


@st.cache_data
def get_all_airport_connectivity(_analyzer: FlightGraphAnalyzer) -> Dict[int, int]:
    """Get connectivity for all airports (cached)"""
    connectivity_map = {}
    if _analyzer.graph:
        for node in _analyzer.graph.nodes():
            connectivity_map[node] = _analyzer.graph.out_degree(node)
    return connectivity_map


def get_airport_connectivity(analyzer: FlightGraphAnalyzer, airport_id: int, connectivity_cache: Optional[Dict[int, int]] = None) -> int:
    """Get number of non-stop destinations for an airport"""
    if connectivity_cache:
        return connectivity_cache.get(airport_id, 0)
    if not analyzer.graph or airport_id not in analyzer.graph.nodes():
        return 0
    return analyzer.graph.out_degree(airport_id)


def get_airport_color(connectivity: int) -> str:
    """Get color for airport based on connectivity"""
    if connectivity > 100:
        return '#1e3a8a'  # Dark blue
    elif connectivity > 30:
        return '#3b82f6'  # Blue
    elif connectivity > 7:
        return '#eab308'  # Yellow
    else:
        return '#ef4444'  # Red


def get_airport_size(connectivity: int) -> int:
    """Get size for airport marker based on connectivity"""
    if connectivity > 100:
        return 8
    elif connectivity > 30:
        return 6
    elif connectivity > 7:
        return 4
    else:
        return 3


def create_flightconnections_map(
    analyzer: FlightGraphAnalyzer,
    source_iata: Optional[str] = None,
    dest_iata: Optional[str] = None,
    all_routes: Optional[List[Dict]] = None,
    selected_route_idx: Optional[int] = None
) -> folium.Map:
    """
    Create FlightConnections-style map with airports and routes
    
    Args:
        analyzer: FlightGraphAnalyzer instance
        source_iata: Source airport IATA (optional)
        dest_iata: Destination airport IATA (optional)
        all_routes: List of all routes to display
        selected_route_idx: Index of selected route to highlight
    """
    # Default center
    center_lat, center_lon = 20, 0
    
    # Create map with light theme
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=2,
        tiles='CartoDB positron',  # Light theme
        attr='CartoDB'
    )
    
    # Add airports only if no routes are provided (for better performance)
    # When routes are shown, airports are already marked on the route
    if not all_routes or selected_route_idx is None:
        airports_df = analyzer.airports_df
        # Reduce number of airports for better performance
        max_airports = 150  # Reduced from 200
        sample_airports = airports_df[airports_df['iata'].notna()].sample(min(max_airports, len(airports_df)))
        
        # Get connectivity cache once
        connectivity_cache = get_all_airport_connectivity(analyzer)
        
        # Batch process airports
        airports_to_add = []
        for _, airport in sample_airports.iterrows():
            lat = airport.get('latitude', 0)
            lon = airport.get('longitude', 0)
            iata = airport.get('iata', '')
            
            if lat != 0 and lon != 0:
                airport_id = analyzer._get_airport_id_by_iata(iata)
                if airport_id:
                    connectivity = get_airport_connectivity(analyzer, airport_id, connectivity_cache)
                    color = get_airport_color(connectivity)
                    size = get_airport_size(connectivity)
                    
                    airport_info = analyzer._get_airport_info(airport_id)
                    name = airport_info.get('name', '') if airport_info else ''
                    city = airport_info.get('city', '') if airport_info else ''
                    
                    airports_to_add.append({
                        'lat': lat,
                        'lon': lon,
                        'iata': iata,
                        'connectivity': connectivity,
                        'color': color,
                        'size': size,
                        'name': name,
                        'city': city
                    })
        
        # Add all airports at once (faster)
        for airport_data in airports_to_add:
            folium.CircleMarker(
                [airport_data['lat'], airport_data['lon']],
                radius=airport_data['size'],
                popup=folium.Popup(
                    f"""
                    <div style="font-family: Arial; min-width: 200px;">
                        <h3 style="margin: 0; color: #1f2937;">{airport_data['iata']}</h3>
                        <p style="margin: 0.5rem 0; color: #6b7280;">{airport_data['name']}</p>
                        <p style="margin: 0; color: #6b7280; font-size: 0.85rem;">{airport_data['city']}</p>
                        <p style="margin: 0.5rem 0 0 0; color: #111827; font-size: 0.85rem;">
                            <strong>Connections:</strong> {airport_data['connectivity']}
                        </p>
                    </div>
                    """,
                    max_width=250
                ),
                tooltip=f"{airport_data['iata']} - {airport_data['connectivity']} connections",
                color=airport_data['color'],
                fillColor=airport_data['color'],
                fillOpacity=0.8,
                weight=1
            ).add_to(m)
    
    # Add routes if provided
    if all_routes and selected_route_idx is not None and selected_route_idx < len(all_routes):
        # Add all routes (non-selected in light gray)
        for i, route in enumerate(all_routes):
            # Handle round trip paths
            if route.get('trip_type') == 'round_trip':
                outbound = route.get('outbound', {})
                return_route = route.get('return', {})
                
                # Outbound path
                outbound_path = outbound.get('path', [])
                if outbound_path:
                    outbound_coords = analyzer.get_airport_coordinates(outbound_path)
                    outbound_route_coords = [(lat, lon) for lat, lon, _ in outbound_coords]
                    
                    if i == selected_route_idx:
                        folium.PolyLine(
                            outbound_route_coords,
                            color='#3b82f6',
                            weight=4,
                            opacity=0.9,
                            smooth_factor=1.0
                        ).add_to(m)
                    else:
                        folium.PolyLine(
                            outbound_route_coords,
                            color='#9ca3af',
                            weight=1,
                            opacity=0.3,
                            smooth_factor=1.0
                        ).add_to(m)
                
                # Return path
                return_path = return_route.get('path', [])
                if return_path:
                    return_coords = analyzer.get_airport_coordinates(return_path)
                    return_route_coords = [(lat, lon) for lat, lon, _ in return_coords]
                    
                    if i == selected_route_idx:
                        folium.PolyLine(
                            return_route_coords,
                            color='#3b82f6',
                            weight=4,
                            opacity=0.9,
                            smooth_factor=1.0
                        ).add_to(m)
                    else:
                        folium.PolyLine(
                            return_route_coords,
                            color='#9ca3af',
                            weight=1,
                            opacity=0.3,
                            smooth_factor=1.0
                        ).add_to(m)
                
                # Add markers for selected round trip
                if i == selected_route_idx:
                    # Outbound airports
                    for j, (lat, lon, iata) in enumerate(outbound_coords):
                        if lat != 0 and lon != 0:
                            marker_color = '#22c55e' if j == 0 else '#3b82f6'
                            folium.CircleMarker(
                                [lat, lon],
                                radius=6,
                                popup=iata,
                                tooltip=iata,
                                color='white',
                                fillColor=marker_color,
                                fillOpacity=1.0,
                                weight=2
                            ).add_to(m)
                    
                    # Return airports (skip first as it's same as outbound destination)
                    for j, (lat, lon, iata) in enumerate(return_coords[1:], len(outbound_coords)):
                        if lat != 0 and lon != 0:
                            marker_color = '#ef4444' if j == len(return_coords) - 1 + len(outbound_coords) - 1 else '#3b82f6'
                            folium.CircleMarker(
                                [lat, lon],
                                radius=6,
                                popup=iata,
                                tooltip=iata,
                                color='white',
                                fillColor=marker_color,
                                fillOpacity=1.0,
                                weight=2
                            ).add_to(m)
            else:
                # One way route
                path = route.get('path', [])
                if path:
                    path_coordinates = analyzer.get_airport_coordinates(path)
                    route_coords = [(lat, lon) for lat, lon, _ in path_coordinates]
                    
                    if i == selected_route_idx:
                        # Selected route - bright blue
                        folium.PolyLine(
                            route_coords,
                            color='#3b82f6',
                            weight=4,
                            opacity=0.9,
                            smooth_factor=1.0
                        ).add_to(m)
                        
                        # Add markers for selected route airports
                        for j, (lat, lon, iata) in enumerate(path_coordinates):
                            if lat != 0 and lon != 0:
                                if j == 0:
                                    marker_color = '#22c55e'  # Green for origin
                                elif j == len(path_coordinates) - 1:
                                    marker_color = '#ef4444'  # Red for destination
                                else:
                                    marker_color = '#3b82f6'  # Blue for transit
                                
                                folium.CircleMarker(
                                    [lat, lon],
                                    radius=6,
                                    popup=iata,
                                    tooltip=iata,
                                    color='white',
                                    fillColor=marker_color,
                                    fillOpacity=1.0,
                                    weight=2
                                ).add_to(m)
                    else:
                        # Other routes - light gray
                        folium.PolyLine(
                            route_coords,
                            color='#9ca3af',
                            weight=1,
                            opacity=0.3,
                            smooth_factor=1.0
                        ).add_to(m)
    
    # Add airport legend
    legend_html = """
    <div class="airport-legend">
        <div class="legend-title">Airport Connections</div>
        <div class="legend-item">
            <div class="legend-dot" style="background: #1e3a8a;"></div>
            <span>> 100 destinations</span>
        </div>
        <div class="legend-item">
            <div class="legend-dot" style="background: #3b82f6;"></div>
            <span>> 30 destinations</span>
        </div>
        <div class="legend-item">
            <div class="legend-dot" style="background: #eab308;"></div>
            <span>> 7 destinations</span>
        </div>
        <div class="legend-item">
            <div class="legend-dot" style="background: #ef4444;"></div>
            <span>< 7 destinations</span>
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m


def render_route_info_panel(route: Dict[str, Any], analyzer: FlightGraphAnalyzer):
    """Render route information panel"""
    if "error" in route:
        st.error(route['error'])
        return
    
    # Handle round trip
    if route.get('trip_type') == 'round_trip':
        outbound = route.get('outbound', {})
        return_route = route.get('return', {})
        time_info = route.get('time_info', {})
        
        st.markdown(f"""
        <div class="route-panel">
            <div class="route-header">
                {route['source']} ⇄ {route['destination']} (Round Trip)
            </div>
            <div class="route-metrics">
                <div class="metric-box">
                    <div class="metric-label">Total Distance</div>
                    <div class="metric-value">{route['total_distance_km']:,.0f} km</div>
                </div>
                <div class="metric-box">
                    <div class="metric-label">Total Stops</div>
                    <div class="metric-value">{route.get('stops', 0)}</div>
                </div>
                <div class="metric-box">
                    <div class="metric-label">Total Time</div>
                    <div class="metric-value">{format_time_hours(time_info.get('total_time', 0))}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### Outbound")
        if outbound:
            render_single_route_details(outbound, analyzer)
        
        st.markdown("### Return")
        if return_route:
            render_single_route_details(return_route, analyzer)
        
        return
    
    # One way trip
    time_info = route.get('time_info', {})
    
    st.markdown(f"""
    <div class="route-panel">
        <div class="route-header">
            {route['source']} → {route['destination']}
        </div>
        <div class="route-metrics">
            <div class="metric-box">
                <div class="metric-label">Distance</div>
                <div class="metric-value">{route['total_distance_km']:,.0f} km</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">Stops</div>
                <div class="metric-value">{route.get('stops', 0)}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">Total Time</div>
                <div class="metric-value">{format_time_hours(time_info.get('total_time', 0))}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">Flight Time</div>
                <div class="metric-value">{format_time_hours(time_info.get('flight_time', 0))}</div>
            </div>
        </div>
        <div style="margin-top: 1rem;">
            <div style="font-size: 0.85rem; color: #6b7280; margin-bottom: 0.5rem;">Route Path</div>
            <div style="font-weight: 500; color: #1f2937;">{' → '.join(route.get('path', []))}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    render_single_route_details(route, analyzer)


def render_single_route_details(route: Dict[str, Any], analyzer: FlightGraphAnalyzer):
    """Render details for a single route (used for round trip)"""
    # Flight legs
    if route.get('legs'):
        st.markdown("**Flight Legs**")
        for i, leg in enumerate(route['legs'], 1):
            transit_delay_html = ""
            if i < len(route['legs']):
                transit_id = analyzer._get_airport_id_by_iata(leg['to'])
                if transit_id:
                    delay = analyzer._get_transit_delay(transit_id)
                    if delay > 0:
                        transit_delay_html = f" • Transit: {format_time_hours(delay)}"
            
            flight_time = format_time_hours(leg.get('flight_time_hours', 0))
            
            st.markdown(f"""
            <div class="leg-item">
                <div class="leg-route">Leg {i}: {leg['from']} → {leg['to']}</div>
                <div class="leg-details">
                    Distance: {leg['distance_km']:,.0f} km • Time: {flight_time} • Airline: {leg.get('airline', 'N/A')}{transit_delay_html}
                </div>
            </div>
            """, unsafe_allow_html=True)


def main():
    """Main client-side application"""
    
    # Load data
    with st.spinner("Loading flight data..."):
        analyzer = load_data()
    
    if analyzer is None:
        st.error("Failed to load data. Please check if the cleaned data files exist.")
        return
    
    # Top Header
    col_logo, col_search, col_actions = st.columns([2, 6, 1])
    
    with col_logo:
        st.markdown('<div class="logo">Flight Route Advisor</div>', unsafe_allow_html=True)
    
    with col_search:
        col_from, col_swap, col_to = st.columns([5, 1, 5])
        
        with col_from:
            # Initialize session state
            if 'client_source_value' not in st.session_state:
                airports_df = analyzer.airports_df
                airport_df = airports_df[airports_df['iata'].notna()].copy()
                airport_df = airport_df.sort_values(by='iata')
                airport_options = airport_df['iata'].tolist()
                st.session_state['client_source_value'] = airport_options[0] if airport_options else None
                st.session_state['client_dest_value'] = airport_options[min(1, len(airport_options) - 1)] if len(airport_options) > 1 else airport_options[0] if airport_options else None
            
            # Handle swap
            swap_clicked = False
            with col_swap:
                swap_clicked = st.button("⇄", use_container_width=True, key="swap_button", help="Swap airports")
            
            if swap_clicked:
                temp = st.session_state['client_source_value']
                st.session_state['client_source_value'] = st.session_state['client_dest_value']
                st.session_state['client_dest_value'] = temp
                st.rerun()
            
            # Get airport options
            airports_df = analyzer.airports_df
            airport_df = airports_df[airports_df['iata'].notna()].copy()
            airport_df = airport_df.sort_values(by='iata')
            airport_options = airport_df['iata'].tolist()
            airport_labels = get_airport_display_map(airports_df)
            format_func = lambda code: airport_labels.get(code, code)
            
            # Get current values
            current_source = st.session_state.get('client_source_value', airport_options[0] if airport_options else None)
            current_dest = st.session_state.get('client_dest_value', airport_options[min(1, len(airport_options) - 1)] if len(airport_options) > 1 else airport_options[0] if airport_options else None)
            
            # Find indices
            try:
                current_source_idx = airport_options.index(current_source) if current_source in airport_options else 0
            except (ValueError, AttributeError):
                current_source_idx = 0
            
            try:
                current_dest_idx = airport_options.index(current_dest) if current_dest in airport_options else min(1, len(airport_options) - 1) if len(airport_options) > 1 else 0
            except (ValueError, AttributeError):
                current_dest_idx = min(1, len(airport_options) - 1) if len(airport_options) > 1 else 0
            
            source_airport = st.selectbox(
                "From",
                airport_options,
                key="client_source",
                format_func=format_func,
                index=current_source_idx,
                label_visibility="collapsed"
            )
            st.session_state['client_source_value'] = source_airport
        
        with col_to:
            dest_airport = st.selectbox(
                "To",
                airport_options,
                key="client_dest",
                format_func=format_func,
                index=current_dest_idx,
                label_visibility="collapsed"
            )
            st.session_state['client_dest_value'] = dest_airport
    
    # Filter Bar
    st.markdown("---")
    col_trip, col_obj, col_stops, col_search_btn = st.columns([2, 3, 2, 2])
    
    with col_trip:
        st.markdown('<div style="font-size: 0.85rem; color: #6b7280; margin-bottom: 0.25rem;">Trip Type</div>', unsafe_allow_html=True)
        trip_type = st.radio(
            "Trip Type",
            ["One Way", "Round Trip"],
            key="client_trip_type",
            horizontal=True,
            label_visibility="collapsed"
        )
    
    with col_obj:
        st.markdown('<div style="font-size: 0.85rem; color: #6b7280; margin-bottom: 0.25rem;">Optimize for</div>', unsafe_allow_html=True)
        objective = st.selectbox(
            "Optimize for",
            ["Shortest Distance", "Fewest Transfers", "Fastest", "Most Popular"],
            key="client_objective",
            label_visibility="collapsed"
        )
    
    with col_stops:
        st.markdown('<div style="font-size: 0.85rem; color: #6b7280; margin-bottom: 0.25rem;">Max Stops</div>', unsafe_allow_html=True)
        max_stops = st.selectbox(
            "Max Stops",
            ["Any", "No stops (0)", "1 stop", "2 stops"],
            key="client_max_stops",
            label_visibility="collapsed"
        )
        max_stops_val = None if max_stops == "Any" else int(max_stops.split()[0]) if max_stops != "No stops (0)" else 0
    
    with col_search_btn:
        st.markdown('<div style="font-size: 0.85rem; color: #6b7280; margin-bottom: 0.25rem;">&nbsp;</div>', unsafe_allow_html=True)
        search_clicked = st.button("Search", type="primary", use_container_width=True)
    
    # Main content: Sidebar + Map
    col_sidebar, col_map = st.columns([1, 3])
    
    with col_sidebar:
        st.markdown("### Route Information")
        
        if search_clicked:
            if source_airport == dest_airport:
                st.warning("Please choose two different airports.")
            else:
                # Check if results are cached
                if trip_type == "Round Trip":
                    outbound_cache_key = get_cache_key(source_airport, dest_airport, max_stops_val, 15)
                    return_cache_key = get_cache_key(dest_airport, source_airport, max_stops_val, 15)
                    is_cached = (
                        'route_cache' in st.session_state and
                        outbound_cache_key in st.session_state.get('route_cache', {}) and
                        return_cache_key in st.session_state.get('route_cache', {})
                    )
                else:
                    cache_key = get_cache_key(source_airport, dest_airport, max_stops_val, 20)
                    is_cached = 'route_cache' in st.session_state and cache_key in st.session_state.get('route_cache', {})
                
                if is_cached:
                    st.info("Using cached results (instant)")
                else:
                    st.info("Searching routes (this may take a moment...)")
                
                with st.spinner("Finding all possible routes..."):
                    objective_map = {
                        "Shortest Distance": "distance",
                        "Fewest Transfers": "transfers",
                        "Fastest": "fastest",
                        "Most Popular": "popular"
                    }
                    objective_key = objective_map.get(objective, "distance")
                    
                    if trip_type == "Round Trip":
                        # Find outbound routes (cached) - reduced for performance
                        outbound_routes = find_routes_cached(
                            analyzer,
                            source_airport,
                            dest_airport,
                            max_stops_val,
                            15  # Reduced from 25
                        )
                        
                        # Find return routes (cached) - reduced for performance
                        return_routes = find_routes_cached(
                            analyzer,
                            dest_airport,
                            source_airport,
                            max_stops_val,
                            15  # Reduced from 25
                        )
                        
                        # Combine outbound and return routes
                        combined_routes = []
                        for outbound in outbound_routes[:10]:  # Limit combinations
                            for return_route in return_routes[:10]:
                                total_distance = outbound['total_distance_km'] + return_route['total_distance_km']
                                total_stops = outbound['stops'] + return_route['stops']
                                
                                outbound_time = outbound.get('time_info', {})
                                return_time = return_route.get('time_info', {})
                                total_time_info = {
                                    'flight_time': outbound_time.get('flight_time', 0) + return_time.get('flight_time', 0),
                                    'transit_time': outbound_time.get('transit_time', 0) + return_time.get('transit_time', 0),
                                    'total_time': outbound_time.get('total_time', 0) + return_time.get('total_time', 0)
                                }
                                
                                combined_routes.append({
                                    'source': source_airport,
                                    'destination': dest_airport,
                                    'trip_type': 'round_trip',
                                    'outbound': outbound,
                                    'return': return_route,
                                    'total_distance_km': total_distance,
                                    'stops': total_stops,
                                    'time_info': total_time_info,
                                    'path': outbound.get('path', [])  # Use outbound path for display
                                })
                        
                        all_routes = combined_routes
                    else:
                        # One way (cached)
                        all_routes = find_routes_cached(
                            analyzer,
                            source_airport,
                            dest_airport,
                            max_stops_val,
                            20  # Reduced from 30 for better performance
                        )
                    
                    if all_routes:
                        # Sort routes based on objective
                        if objective_key == "transfers":
                            all_routes.sort(key=lambda x: x.get('stops', 0))
                        elif objective_key == "distance":
                            all_routes.sort(key=lambda x: x.get('total_distance_km', 0))
                        elif objective_key == "fastest":
                            all_routes.sort(key=lambda x: x.get('time_info', {}).get('total_time', float('inf')))
                        elif objective_key == "popular":
                            def avg_route_count(route):
                                if route.get('trip_type') == 'round_trip':
                                    outbound_legs = route.get('outbound', {}).get('legs', [])
                                    return_legs = route.get('return', {}).get('legs', [])
                                    all_legs = outbound_legs + return_legs
                                else:
                                    all_legs = route.get('legs', [])
                                if all_legs:
                                    return sum(leg.get('route_count', 1) for leg in all_legs) / len(all_legs)
                                return 0
                            all_routes.sort(key=avg_route_count, reverse=True)
                        
                        # Store routes
                        st.session_state['client_all_routes'] = all_routes
                        st.session_state['client_selected_route_idx'] = 0
                    else:
                        st.session_state['client_all_routes'] = []
                        st.session_state['client_selected_route_idx'] = None
                        st.error("No routes found with current constraints")
        
        # Display routes list
        if 'client_all_routes' in st.session_state and st.session_state.get('client_all_routes'):
            all_routes = st.session_state['client_all_routes']
            st.markdown(f"**Found {len(all_routes)} route(s)**")
            
            # Route selector dropdown
            selected_idx = st.session_state.get('client_selected_route_idx', 0)
            
            route_options = []
            for i, r in enumerate(all_routes):
                route_type = "Round Trip" if r.get('trip_type') == 'round_trip' else "One Way"
                stops = r.get('stops', 0)
                distance = r['total_distance_km']
                time_info = r.get('time_info', {})
                total_time = format_time_hours(time_info.get('total_time', 0))
                route_options.append(f"Route {i+1}: {route_type} - {stops} stops, {distance:,.0f} km, {total_time}")
            
            new_selected_idx = st.selectbox(
                "Select route",
                range(len(route_options)),
                format_func=lambda x: route_options[x],
                key="route_selector",
                index=selected_idx
            )
            
            if new_selected_idx != selected_idx:
                st.session_state['client_selected_route_idx'] = new_selected_idx
                st.rerun()
            
            # Display selected route info
            if new_selected_idx < len(all_routes):
                st.markdown("---")
                render_route_info_panel(all_routes[new_selected_idx], analyzer)
        else:
            st.info("Select airports and click Search to find routes.")
    
    with col_map:
        # Map visualization
        if 'client_all_routes' in st.session_state and st.session_state.get('client_all_routes'):
            all_routes = st.session_state['client_all_routes']
            selected_idx = st.session_state.get('client_selected_route_idx', 0)
            
            m = create_flightconnections_map(
                analyzer,
                source_airport,
                dest_airport,
                all_routes,
                selected_idx
            )
            
            st_folium(m, width=None, height=700, returned_objects=[])
        else:
            # Default map view
            m = create_flightconnections_map(analyzer)
            st_folium(m, width=None, height=700, returned_objects=[])


if __name__ == "__main__":
    main()
