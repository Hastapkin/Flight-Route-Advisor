"""
Flight Route Advisor - Streamlit Application
Google Flights inspired UI for flight route analysis
"""

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from typing import Dict, List, Tuple, Any
import sys
from pathlib import Path

# Add pipeline to path
sys.path.append(str(Path(__file__).parent.parent))

from pipeline.graph_analyzer import FlightGraphAnalyzer, create_flight_analyzer


# Page configuration
st.set_page_config(
    page_title="Flight Route Advisor",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS - Google Flights style
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: 400;
        color: #202124;
        margin-bottom: 1rem;
    }
    .search-container {
        background: white;
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        margin-bottom: 2rem;
    }
    .route-result-card {
        background: white;
        border: 1px solid #dadce0;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .route-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    .route-path {
        font-size: 1.1rem;
        font-weight: 500;
        color: #202124;
    }
    .route-meta {
        display: flex;
        gap: 1rem;
        color: #5f6368;
        font-size: 0.9rem;
    }
    .hub-card {
        background: #f8f9fa;
        border-left: 3px solid #1a73e8;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
        border-radius: 4px;
    }
    .metric-badge {
        background: #e8f0fe;
        color: #1a73e8;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    .stButton>button {
        background-color: #1a73e8;
        color: white;
        border-radius: 4px;
        border: none;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
    }
    .stButton>button:hover {
        background-color: #1557b0;
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


def get_airport_display_map(airports_df: pd.DataFrame) -> Dict[str, str]:
    """Return mapping from IATA to descriptive label"""
    display_map = {}
    for _, airport in airports_df.iterrows():
        if pd.notna(airport.get('iata')):
            iata = str(airport.get('iata', ''))
            name = str(airport.get('name', ''))
            city = str(airport.get('city', ''))
            country = str(airport.get('country', ''))
            display_map[iata] = f"{iata} - {name} ({city}, {country})"
    return display_map


def get_popular_routes():
    """Get list of popular routes for quick access"""
    return [
        {"from": "SGN", "to": "LHR", "label": "SGN → LHR (0 transit)", "max_stops": 0},
        {"from": "CDG", "to": "LHR", "label": "CDG → LHR (0 transit)", "max_stops": 0},
        {"from": "SIN", "to": "HKG", "label": "SIN → HKG (0 transit)", "max_stops": 0},
        {"from": "SGN", "to": "LHR", "label": "SGN → LHR (1 transit)", "max_stops": 1},
        {"from": "SGN", "to": "JFK", "label": "SGN → JFK (2 transits)", "max_stops": 2},
        {"from": "HAN", "to": "LAX", "label": "HAN → LAX (2 transits)", "max_stops": 2},
    ]


def create_route_map(coordinates: List[Tuple[float, float, str]], 
                     route_coords: List[Tuple[float, float]] = None) -> folium.Map:
    """Create Folium map with route visualization"""
    if not coordinates:
        return None
    
    center_lat = sum(coord[0] for coord in coordinates) / len(coordinates)
    center_lon = sum(coord[1] for coord in coordinates) / len(coordinates)
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=4)
    
    # Add route line
    if route_coords and len(route_coords) > 1:
        folium.PolyLine(
            route_coords,
            color="#1a73e8",
            weight=3,
            opacity=0.7
        ).add_to(m)
    
    # Add markers
    for lat, lon, iata in coordinates:
        folium.Marker(
            [lat, lon],
            popup=iata,
            icon=folium.Icon(color="blue", icon="plane", prefix="fa")
        ).add_to(m)
    
    return m


def display_route_result(result: Dict[str, Any], analyzer: FlightGraphAnalyzer):
    """Display route result in Google Flights style"""
    if "error" in result:
        st.error(f"❌ {result['error']}")
        return
    
    st.markdown("### ✈️ Route Found")
    
    # Main route card
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"**{' → '.join(result['path'])}**")
        caption_text = f"{result['stops']} stop(s) • {result['total_distance_km']:,.0f} km"
        if result.get('total_route_time_hours'):
            total_hours = int(result['total_route_time_hours'])
            total_mins = int((result['total_route_time_hours'] - total_hours) * 60)
            caption_text += f" • {total_hours}h {total_mins}m"
        st.caption(caption_text)
    with col2:
        st.metric("Distance", f"{result['total_distance_km']:,.0f} km")
    with col3:
        if result.get('total_route_time_hours'):
            total_hours = int(result['total_route_time_hours'])
            total_mins = int((result['total_route_time_hours'] - total_hours) * 60)
            st.metric("Total Time", f"{total_hours}h {total_mins}m")
    
    # Route details
    with st.expander("Route Details", expanded=True):
        leg_times = result.get('leg_times', [])
        transit_times = result.get('transit_times', [])
        
        for i, leg in enumerate(result['legs'], 1):
            leg_info = f"**Leg {i}:** {leg['from']} → {leg['to']} ({leg['distance_km']:,.0f} km"
            if i <= len(leg_times):
                leg_hours = int(leg_times[i-1])
                leg_mins = int((leg_times[i-1] - leg_hours) * 60)
                leg_info += f", {leg_hours}h {leg_mins}m"
            leg_info += ")"
            st.markdown(leg_info)
            
            # Show transit time after each leg (except last)
            if i < len(result['legs']) and i <= len(transit_times):
                transit_hours = int(transit_times[i-1])
                transit_mins = int((transit_times[i-1] - transit_hours) * 60)
                st.markdown(f"  ⏱️ Transit at {leg['to']}: {transit_hours}h {transit_mins}m")
        
        # Summary
        if result.get('total_flight_time_hours') and result.get('total_transit_time_hours'):
            flight_hours = int(result['total_flight_time_hours'])
            flight_mins = int((result['total_flight_time_hours'] - flight_hours) * 60)
            transit_hours = int(result['total_transit_time_hours'])
            transit_mins = int((result['total_transit_time_hours'] - transit_hours) * 60)
            st.markdown("---")
            st.markdown(f"**Flight Time:** {flight_hours}h {flight_mins}m | **Transit Time:** {transit_hours}h {transit_mins}m")
    
    # Map
    path_coordinates = analyzer.get_airport_coordinates(result['path'])
    if path_coordinates:
        route_coords = [(lat, lon) for lat, lon, _ in path_coordinates]
        m = create_route_map(path_coordinates, route_coords)
        if m:
            st_folium(m, width=950, height=520, key="route_map_main")


def display_alternative_paths(result: Dict[str, Any], analyzer: FlightGraphAnalyzer):
    """Display alternative paths"""
    if "error" in result:
        st.warning(result["error"])
        return
    if not result.get('paths'):
        st.warning("No alternative routes found for this transit setting.")
        return

    # Remove routes identical to main route (if available)
    main_path = None
    if 'route_result' in st.session_state and isinstance(st.session_state['route_result'], dict):
        main_path = st.session_state['route_result'].get('path')
    filtered = []
    seen = set()
    for p in result.get('paths', []):
        path_tuple = tuple(p.get('path', []))
        if main_path and p.get('path') == main_path:
            continue
        if path_tuple in seen:
            continue
        seen.add(path_tuple)
        filtered.append(p)
    result['paths'] = filtered
    if not filtered:
        st.warning("No alternative routes different from the main route.")
        return
    
    st.markdown("---")
    st.markdown("### 🔄 Alternative Routes")
    
    for i, path_info in enumerate(result['paths'][:3], 1):
        # Build title with time info
        title = f"Option {i}: {' → '.join(path_info['path'])} ({path_info['stops']} stops, {path_info['distance_km']:,.0f} km"
        if path_info.get('total_route_time_hours'):
            total_hours = int(path_info['total_route_time_hours'])
            total_mins = int((path_info['total_route_time_hours'] - total_hours) * 60)
            title += f", {total_hours}h {total_mins}m"
        title += ")"
        
        with st.expander(title, expanded=(i == 1)):
            info_text = f"**Distance:** {path_info['distance_km']:,.0f} km | **Stops:** {path_info['stops']}"
            if path_info.get('total_route_time_hours'):
                total_hours = int(path_info['total_route_time_hours'])
                total_mins = int((path_info['total_route_time_hours'] - total_hours) * 60)
                info_text += f" | **Total Time:** {total_hours}h {total_mins}m"
            st.markdown(info_text)
            
            if path_info.get('transfer_hubs'):
                st.markdown(f"**Transfer Hubs:** {', '.join(path_info['transfer_hubs'])}")
            
            # Show leg times if available
            if path_info.get('leg_times') and path_info.get('transit_times'):
                st.markdown("**Timeline:**")
                leg_times = path_info['leg_times']
                transit_times = path_info['transit_times']
                # Note: We don't have individual leg details here, so we show summary
                if path_info.get('total_flight_time_hours') and path_info.get('total_transit_time_hours'):
                    flight_hours = int(path_info['total_flight_time_hours'])
                    flight_mins = int((path_info['total_flight_time_hours'] - flight_hours) * 60)
                    transit_hours = int(path_info['total_transit_time_hours'])
                    transit_mins = int((path_info['total_transit_time_hours'] - transit_hours) * 60)
                    st.markdown(f"  Flight: {flight_hours}h {flight_mins}m | Transit: {transit_hours}h {transit_mins}m")
            
            # Map
            path_coordinates = analyzer.get_airport_coordinates(path_info['path'])
            if path_coordinates:
                route_coords = [(lat, lon) for lat, lon, _ in path_coordinates]
                m = create_route_map(path_coordinates, route_coords)
                if m:
                    st_folium(m, width=900, height=450, key=f"alt_map_{i}")


def display_alternative_hubs(result: Dict[str, Any], analyzer: FlightGraphAnalyzer):
    """Display alternative transfer hubs"""
    if "error" in result or not result.get('alternative_hubs'):
        return
    
    st.markdown("---")
    st.markdown("### 🌟 Alternative Transfer Hubs")
    
    # Table
    hubs_data = []
    for hub in result['alternative_hubs'][:5]:
        row = {
            "Hub": hub['hub'],
            "Name": hub['name'],
            "Route": hub['path'],
            "Distance": f"{hub['total_distance_km']:,.0f} km",
            "Efficiency": f"{hub['efficiency_percent']:.1f}%"
        }
        
        # Add time if available
        if hub.get('total_route_time_hours'):
            total_hours = int(hub['total_route_time_hours'])
            total_mins = int((hub['total_route_time_hours'] - total_hours) * 60)
            row["Total Time"] = f"{total_hours}h {total_mins}m"
        
        hubs_data.append(row)
    
    st.dataframe(pd.DataFrame(hubs_data), use_container_width=True)


def main():
    """Main Streamlit application - Google Flights style"""
    
    st.markdown('<h1 class="main-header">Flight Route Advisor</h1>', unsafe_allow_html=True)
    
    # Load data
    with st.spinner("Loading flight network..."):
        analyzer = load_data()
    
    if analyzer is None:
        st.error("Failed to load data. Please run notebook/flight_route.ipynb first.")
        return
    
    # Search Container - Google Flights style
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    
    # Popular routes
    popular_routes = get_popular_routes()
    st.markdown("**Quick searches:**")
    cols = st.columns(len(popular_routes))
    for i, route in enumerate(popular_routes):
        if cols[i].button(route['label'], key=f"quick_{i}"):
            st.session_state['from'] = route['from']
            st.session_state['to'] = route['to']
            st.session_state['max_stops'] = route.get('max_stops', 2)
    
    st.markdown("---")
    
    # Airport selection
    airports_df = analyzer.airports_df
    airport_df = airports_df[airports_df['iata'].notna()].copy().sort_values(by='iata')
    airport_options = airport_df['iata'].tolist()
    airport_labels = get_airport_display_map(airports_df)
    
    col1, col3 = st.columns([3, 3])
    with col1:
        from_airport = st.selectbox(
            "From",
            airport_options,
            key='from',
            format_func=lambda x: airport_labels.get(x, x)
        )
    with col3:
        to_airport = st.selectbox(
            "To",
            airport_options,
            key='to',
            format_func=lambda x: airport_labels.get(x, x)
        )
    
    # Transit constraint + optional heavy computation
    col_opt1, col_opt2, col_opt3 = st.columns(3)
    with col_opt1:
        max_stops = st.selectbox(
            "Max stops (transits)",
            options=[0, 1, 2],
            index=[0, 1, 2].index(st.session_state.get('max_stops', 2)),
            help="Limit number of transit points (commercial itineraries usually ≤2)"
        )
    with col_opt2:
        compute_alt_routes = st.checkbox(
            "Compute alternative routes",
            value=True,
            help="Turn off for faster search"
        )
    with col_opt3:
        compute_alt_hubs = st.checkbox(
            "Compute alternative transfer hubs (slower)",
            value=False,
            help="Turn on to see hub suggestions; may be slower"
        )
    
    # Search button
    if st.button("🔍 Search Flights", type="primary", use_container_width=True):
        if from_airport == to_airport:
            st.warning("Please select different airports")
        else:
            with st.spinner("Finding best route..."):
                # Main route (respect requested max_stops)
                main_result = analyzer.find_optimized_route(from_airport, to_airport, objective="distance", max_stops=max_stops)
                if ("error" in main_result) or (main_result.get("stops") != max_stops):
                    main_result = {"error": f"No route found with exactly {max_stops} transit(s)"}

                # Alternative paths: optional to speed up
                if compute_alt_routes:
                    alt_paths_raw = analyzer.find_robust_transfer_paths(from_airport, to_airport, k=3, max_stops=None)
                    alt_list = alt_paths_raw.get("paths", []) if isinstance(alt_paths_raw, dict) else []
                    main_path = main_result.get("path") if isinstance(main_result, dict) else None
                    alt_filtered = []
                    seen = set()
                    for p in alt_list:
                        path_tuple = tuple(p.get("path", []))
                        if main_path and p.get("path") == main_path:
                            continue
                        if path_tuple in seen:
                            continue
                        seen.add(path_tuple)
                        alt_filtered.append(p)
                    alt_paths = {
                        "paths": alt_filtered,
                        "total_paths_found": len(alt_filtered)
                    }
                    if not alt_filtered:
                        alt_paths = {"error": "No alternative routes available."}
                else:
                    alt_paths = {"error": "Alternative routes not computed (fast mode)."}

                st.session_state['route_result'] = main_result
                st.session_state['alt_paths'] = alt_paths
                
                # Alternative hubs (optional to save time)
                if compute_alt_hubs:
                    alt_hubs = analyzer.suggest_alternative_transfer_hubs(from_airport, to_airport, top_n=5)
                    st.session_state['alt_hubs'] = alt_hubs
                else:
                    st.session_state.pop('alt_hubs', None)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Display results
    if 'route_result' in st.session_state:
        display_route_result(st.session_state['route_result'], analyzer)
        
        if 'alt_paths' in st.session_state:
            display_alternative_paths(st.session_state['alt_paths'], analyzer)
        
        if 'alt_hubs' in st.session_state:
            display_alternative_hubs(st.session_state['alt_hubs'], analyzer)
    
    # Additional tabs for other features
    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["Hub Analysis", "Hub Removal What-If", "Network Stats"])
    
    with tab1:
        st.markdown("### Hub Explorer")
        country_options = ["Global"] + sorted(airports_df['country'].dropna().unique().tolist())
        selected_country = st.selectbox("Country", country_options)
        top_n = st.slider("Top N hubs", 5, 20, 10)
        
        if st.button("Analyze Hubs"):
            with st.spinner("Analyzing hubs..."):
                country_filter = None if selected_country == "Global" else selected_country
                result = analyzer.analyze_hubs(country_filter, top_n)
                st.session_state['hub_result'] = result
        
        if 'hub_result' in st.session_state:
            result = st.session_state['hub_result']
            if "error" not in result:
                st.markdown(f"**Top {len(result['top_hubs'])} Hubs:**")
                for i, hub in enumerate(result['top_hubs'], 1):
                    st.markdown(f"{i}. **{hub['airport']}** - {hub['name']} ({hub['city']}, {hub['country']})")
                    st.caption(f"Degree: {hub['degree_centrality']:.4f} | Betweenness: {hub['betweenness_centrality']:.4f}")
    
    with tab2:
        st.markdown("### Hub Removal What-If Analysis")
        hub_options = sorted(airport_options)
        selected_hub = st.selectbox("Hub to remove", hub_options)
        
        if st.button("Analyze Impact"):
            with st.spinner("Simulating removal..."):
                result = analyzer.hub_removal_analysis(selected_hub)
                st.session_state['removal_result'] = result
        
        if 'removal_result' in st.session_state:
            result = st.session_state['removal_result']
            if "error" not in result:
                st.markdown(f"**Impact Severity:** {result['severity']}")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Routes Affected", result['affected_routes_count'])
                with col2:
                    st.metric("Edges Lost", result['impact_metrics']['edges_lost'])
                with col3:
                    st.metric("Components Increase", result['impact_metrics']['components_increase'])
    
    with tab3:
        st.markdown("### Network Statistics")
        stats = analyzer.get_network_stats()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Airports", f"{stats['total_nodes']:,}")
        with col2:
            st.metric("Routes", f"{stats['total_edges']:,}")
        with col3:
            st.metric("Density", f"{stats['density']:.4f}")


if __name__ == "__main__":
    main()
