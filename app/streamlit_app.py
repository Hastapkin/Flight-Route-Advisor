"""
Flight Route Advisor - Streamlit Application
Interactive flight route analysis with map visualization
"""

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import networkx as nx
from typing import Dict, List, Tuple, Any
import json
import sys
from pathlib import Path

# Add pipeline to path
sys.path.append(str(Path(__file__).parent.parent))

from pipeline.graph_analyzer import FlightGraphAnalyzer, create_flight_analyzer


# Page configuration
st.set_page_config(
    page_title="Flight Route Advisor",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .route-info {
        background-color: #e8f4fd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .hub-card {
        background-color: #fff2e8;
        padding: 0.8rem;
        border-radius: 0.5rem;
        margin: 0.3rem 0;
        border-left: 3px solid #ff7f0e;
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


def search_airports(airports_df, search_term: str, limit: int = 20):
    """Search airports by IATA, name, city, or country"""
    if not search_term:
        return []
    
    search_term = search_term.upper()
    results = []
    
    for _, airport in airports_df.iterrows():
        if pd.isna(airport.get('iata')):
            continue
            
        iata = str(airport.get('iata', '')).upper()
        name = str(airport.get('name', '')).upper()
        city = str(airport.get('city', '')).upper()
        country = str(airport.get('country', '')).upper()
        
        if (search_term in iata or 
            search_term in name or 
            search_term in city or 
            search_term in country):
            results.append({
                'iata': airport.get('iata', ''),
                'name': airport.get('name', ''),
                'city': airport.get('city', ''),
                'country': airport.get('country', ''),
                'display': f"{airport.get('iata', '')} - {airport.get('name', '')} ({airport.get('city', '')}, {airport.get('country', '')})"
            })
            if len(results) >= limit:
                break
    
    return results


def get_airport_info(airports_df, iata: str):
    """Get airport information by IATA code"""
    airport = airports_df[airports_df['iata'] == iata]
    if not airport.empty:
        return {
            'iata': airport.iloc[0].get('iata', ''),
            'name': airport.iloc[0].get('name', ''),
            'city': airport.iloc[0].get('city', ''),
            'country': airport.iloc[0].get('country', ''),
            'latitude': airport.iloc[0].get('latitude', 0),
            'longitude': airport.iloc[0].get('longitude', 0)
        }
    return None


def get_popular_routes():
    """Get list of popular routes for quick access"""
    return [
        {"from": "SGN", "to": "LHR", "label": "Ho Chi Minh -> London"},
        {"from": "SGN", "to": "JFK", "label": "Ho Chi Minh -> New York"},
        {"from": "HAN", "to": "NRT", "label": "Hanoi -> Tokyo"},
        {"from": "SGN", "to": "DXB", "label": "Ho Chi Minh -> Dubai"},
        {"from": "BKK", "to": "LHR", "label": "Bangkok -> London"},
        {"from": "SIN", "to": "JFK", "label": "Singapore -> New York"},
        {"from": "NRT", "to": "LAX", "label": "Tokyo -> Los Angeles"},
        {"from": "CDG", "to": "JFK", "label": "Paris -> New York"},
    ]


def get_connected_airports_count(analyzer, iata: str):
    """Get number of airports connected to a given airport"""
    try:
        airport_id = analyzer._get_airport_id_by_iata(iata)
        if airport_id and analyzer.graph:
            if airport_id in analyzer.graph.nodes():
                out_degree = analyzer.graph.out_degree(airport_id)
                in_degree = analyzer.graph.in_degree(airport_id)
                return out_degree + in_degree
    except:
        pass
    return 0


def create_airport_map(coordinates: List[Tuple[float, float, str]], 
                      route_coordinates: List[Tuple[float, float]] = None,
                      center_lat: float = None, 
                      center_lon: float = None) -> folium.Map:
    """
    Create Folium map with airports and routes
    
    Args:
        coordinates: List of (lat, lon, iata) tuples
        route_coordinates: List of (lat, lon) tuples for route path
        center_lat: Center latitude
        center_lon: Center longitude
        
    Returns:
        Folium map object
    """
    # Calculate center if not provided
    if center_lat is None or center_lon is None:
        if coordinates:
            center_lat = sum(coord[0] for coord in coordinates) / len(coordinates)
            center_lon = sum(coord[1] for coord in coordinates) / len(coordinates)
        else:
            center_lat, center_lon = 20, 0  # Default center
    
    # Create map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=3,
        tiles='OpenStreetMap'
    )
    
    # Add airports
    for lat, lon, iata in coordinates:
        if lat != 0 and lon != 0:  # Valid coordinates
            folium.Marker(
                [lat, lon],
                popup=f"<b>{iata}</b>",
                tooltip=iata
            ).add_to(m)
    
    # Add route line
    if route_coordinates and len(route_coordinates) > 1:
        folium.PolyLine(
            route_coordinates,
            color='red',
            weight=3,
            opacity=0.8,
            popup="Flight Route"
        ).add_to(m)
    
    return m


def display_shortest_path_result(result: Dict[str, Any], analyzer: FlightGraphAnalyzer):
    """Display shortest path analysis results"""
    if "error" in result:
        error_msg = result['error']
        st.error(error_msg)
        
        # Provide helpful suggestions
        if "No path found" in error_msg:
            st.warning("Suggestions:")
            st.markdown("""
            - Try selecting airports with more connections (major hubs)
            - Check if both airports are in the network
            - Some airports may not have direct or connecting routes
            """)
            
            # Suggest nearby hubs
            if 'source' in result or 'destination' in result:
                st.info("Tip: Try using major hubs as transfer points. Go to 'Hub Analysis' to see top airports with most connections.")
        
        return
    
    # Success message
    st.success(f"Route found from {result['source']} to {result['destination']}!")
    
    # Route information
    st.markdown("### Route Information")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Distance", f"{result['total_distance_km']:,.0f} km")
    
    with col2:
        st.metric("Number of Stops", f"{result['stops']}")
    
    with col3:
        st.metric("Flight Legs", f"{len(result['legs'])}")
    
    # Route details
    st.markdown("### Route Details")
    
    route_info = f"""
    **From:** {result['source']} -> **To:** {result['destination']}
    
    **Path:** {' -> '.join(result['path'])}
    
    **Total Distance:** {result['total_distance_km']:,.0f} km
    **Stops:** {result['stops']}
    """
    
    st.markdown(route_info)
    
    # Flight legs table
    if result['legs']:
        legs_data = []
        for i, leg in enumerate(result['legs'], 1):
            legs_data.append({
                "Leg": i,
                "From": leg['from'],
                "To": leg['to'],
                "Distance (km)": f"{leg['distance_km']:,.0f}"
            })
        
        legs_df = pd.DataFrame(legs_data)
        st.dataframe(legs_df, use_container_width=True)
    
    # Map visualization
    st.markdown("### Route Map")
    
    # Get coordinates for airports in path
    path_coordinates = analyzer.get_airport_coordinates(result['path'])
    
    if path_coordinates:
        # Create route line coordinates
        route_coords = [(lat, lon) for lat, lon, _ in path_coordinates]
        
        # Create map
        center_lat = sum(coord[0] for coord in path_coordinates) / len(path_coordinates)
        center_lon = sum(coord[1] for coord in path_coordinates) / len(path_coordinates)
        
        m = create_airport_map(
            path_coordinates, 
            route_coords,
            center_lat, 
            center_lon
        )
        
        # Display map
        st_folium(m, width=700, height=500)


def display_hub_analysis_result(result: Dict[str, Any]):
    """Display hub analysis results"""
    if "error" in result:
        st.error(result['error'])
        return
    
    st.markdown(f"### Hub Analysis - {result['country']}")
    
    # Summary metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Airports", result['total_airports'])
    
    with col2:
        st.metric("Top Hubs Shown", len(result['top_hubs']))
    
    # Top hubs
    st.markdown("### Top Hubs")
    
    for i, hub in enumerate(result['top_hubs'], 1):
        with st.container():
            st.markdown(f"""
            <div class="hub-card">
                <h4>#{i} {hub['airport']} - {hub['name']}</h4>
                <p><strong>Location:</strong> {hub['city']}, {hub['country']}</p>
                <p><strong>Degree Centrality:</strong> {hub['degree_centrality']:.4f}</p>
                <p><strong>Betweenness Centrality:</strong> {hub['betweenness_centrality']:.4f}</p>
                <p><strong>PageRank:</strong> {hub['pagerank']:.4f}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Backup hubs
    if result['backup_hubs']:
        st.markdown("### Backup Hubs")
        
        backup_data = []
        for hub in result['backup_hubs']:
            backup_data.append({
                "Airport": hub['airport'],
                "Name": hub['name'],
                "City": hub['city'],
                "Country": hub['country'],
                "Degree Centrality": f"{hub['degree_centrality']:.4f}",
                "PageRank": f"{hub['pagerank']:.4f}"
            })
        
        backup_df = pd.DataFrame(backup_data)
        st.dataframe(backup_df, use_container_width=True)


def display_hub_removal_result(result: Dict[str, Any]):
    """Display hub removal analysis results"""
    if "error" in result:
        st.error(result['error'])
        return
    
    st.markdown(f"### Hub Removal Analysis - {result['hub_removed']}")
    
    # Hub info
    hub_info = result['hub_info']
    if hub_info:
        st.markdown(f"**Hub:** {hub_info['name']} ({hub_info['city']}, {hub_info['country']})")
    
    # Impact severity
    severity = result['severity']
    st.markdown(f"**Impact Severity:** {severity}")
    
    # Impact metrics
    st.markdown("### Impact Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Nodes Lost", result['impact_metrics']['nodes_lost'])
    
    with col2:
        st.metric("Edges Lost", result['impact_metrics']['edges_lost'])
    
    with col3:
        st.metric("Density Change", f"{result['impact_metrics']['density_change']:.4f}")
    
    with col4:
        st.metric("Components Increase", result['impact_metrics']['components_increase'])
    
    # Network comparison
    st.markdown("### Network Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Before Removal:**")
        original = result['original_stats']
        st.write(f"- Nodes: {original['total_nodes']:,}")
        st.write(f"- Edges: {original['total_edges']:,}")
        st.write(f"- Density: {original['density']:.4f}")
        st.write(f"- Strongly Connected: {'Yes' if original['is_strongly_connected'] else 'No'}")
    
    with col2:
        st.markdown("**After Removal:**")
        remaining = result['remaining_stats']
        st.write(f"- Nodes: {remaining['total_nodes']:,}")
        st.write(f"- Edges: {remaining['total_edges']:,}")
        st.write(f"- Density: {remaining['density']:.4f}")
        st.write(f"- Strongly Connected: {'Yes' if remaining['is_strongly_connected'] else 'No'}")
    
    # Affected routes
    st.markdown("### Affected Routes")
    st.write(f"**Total Routes Affected:** {result['affected_routes_count']}")
    
    if result['affected_routes']:
        st.markdown("**Sample Affected Routes:**")
        routes_data = []
        for route in result['affected_routes']:
            routes_data.append({
                "From": route['from'],
                "To": route['to'],
                "Distance (km)": f"{route['distance_km']:,.0f}"
            })
        
        routes_df = pd.DataFrame(routes_data)
        st.dataframe(routes_df, use_container_width=True)
    
    # Alternative paths
    if result['alternative_paths']:
        st.markdown("### Alternative Paths")
        
        alt_data = []
        for alt in result['alternative_paths']:
            if alt['alternative_path'] != "NO_ALTERNATIVE":
                alt_data.append({
                    "Original Route": f"{alt['original_from']} -> {alt['original_to']}",
                    "Alternative Path": " -> ".join(alt['alternative_path']),
                    "Distance (km)": f"{alt['alternative_distance']:,.0f}",
                    "Stops": alt['path_length']
                })
            else:
                alt_data.append({
                    "Original Route": f"{alt['original_from']} -> {alt['original_to']}",
                    "Alternative Path": "NO ALTERNATIVE",
                    "Distance (km)": "Infinity",
                    "Stops": "N/A"
                })
        
        alt_df = pd.DataFrame(alt_data)
        st.dataframe(alt_df, use_container_width=True)


def display_network_stats(analyzer: FlightGraphAnalyzer):
    """Display network statistics"""
    stats = analyzer.get_network_stats()
    
    st.markdown("### Network Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Airports", f"{stats['total_nodes']:,}")
    
    with col2:
        st.metric("Total Routes", f"{stats['total_edges']:,}")
    
    with col3:
        st.metric("Network Density", f"{stats['density']:.4f}")
    
    # Connectivity info
    st.markdown("#### Connectivity")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Strongly Connected", "Yes" if stats['is_strongly_connected'] else "No")
        st.metric("Strong Components", stats['number_of_strongly_connected_components'])
    
    with col2:
        st.metric("Weakly Connected", "Yes" if stats['is_weakly_connected'] else "No")
        st.metric("Weak Components", stats['number_of_weakly_connected_components'])


def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown('<h1 class="main-header">Flight Route Advisor</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Load data
    with st.spinner("Loading flight data..."):
        analyzer = load_data()
    
    if analyzer is None:
        st.error("Failed to load data. Please check if the cleaned data files exist in 'data/cleaned/' directory.")
        return
    
    # Sidebar
    st.sidebar.markdown("## Controls")
    
    # Mode selection
    mode = st.sidebar.selectbox(
        "Select Analysis Mode",
        ["Shortest Route", "Hub Analysis", "Hub Removal What-If", "Network Overview"]
    )
    
    st.sidebar.markdown("---")
    
    if mode == "Shortest Route":
        st.sidebar.markdown("### Find Shortest Route")
        
        # Popular routes quick access
        st.sidebar.markdown("#### Quick Examples")
        popular_routes = get_popular_routes()
        
        cols = st.sidebar.columns(2)
        for i, route in enumerate(popular_routes[:4]):  # Show first 4
            col_idx = i % 2
            if cols[col_idx].button(f"{route['from']}->{route['to']}", key=f"quick_{i}", use_container_width=True):
                st.session_state['quick_from'] = route['from']
                st.session_state['quick_to'] = route['to']
        
        st.sidebar.markdown("---")
        
        # Airport search
        airports_df = analyzer.airports_df
        airport_options = airports_df[airports_df['iata'].notna()]['iata'].sort_values().tolist()
        
        # Search for source airport
        st.sidebar.markdown("#### Search Airport")
        search_from = st.sidebar.text_input("Search From Airport (IATA, Name, City)", 
                                           value=st.session_state.get('quick_from', ''),
                                           key="search_from",
                                           placeholder="e.g., SGN, Ho Chi Minh, or Vietnam")
        
        if search_from:
            search_results_from = search_airports(airports_df, search_from, limit=10)
            if search_results_from:
                selected_from_display = st.sidebar.selectbox(
                    "Select From Airport",
                    options=[r['display'] for r in search_results_from],
                    key="select_from_display"
                )
                source_airport = next((r['iata'] for r in search_results_from if r['display'] == selected_from_display), None)
            else:
                st.sidebar.warning("No airports found. Try different search term.")
                source_airport = None
        else:
            # Fallback to selectbox if no search
            default_index = 0
            if st.session_state.get('quick_from') and st.session_state.get('quick_from') in airport_options:
                default_index = airport_options.index(st.session_state.get('quick_from'))
            source_airport = st.sidebar.selectbox("From Airport", airport_options, index=default_index, key="from_selectbox")
        
        # Show airport info if selected
        if source_airport:
            airport_info = get_airport_info(airports_df, source_airport)
            if airport_info:
                connected_count = get_connected_airports_count(analyzer, source_airport)
                st.sidebar.info(f"**{airport_info['name']}**\n{airport_info['city']}, {airport_info['country']}\n{connected_count} connections")
        
        # Search for destination airport
        search_to = st.sidebar.text_input("Search To Airport (IATA, Name, City)", 
                                          value=st.session_state.get('quick_to', ''),
                                          key="search_to",
                                          placeholder="e.g., LHR, London, or UK")
        
        if search_to:
            search_results_to = search_airports(airports_df, search_to, limit=10)
            if search_results_to:
                selected_to_display = st.sidebar.selectbox(
                    "Select To Airport",
                    options=[r['display'] for r in search_results_to],
                    key="select_to_display"
                )
                dest_airport = next((r['iata'] for r in search_results_to if r['display'] == selected_to_display), None)
            else:
                st.sidebar.warning("No airports found. Try different search term.")
                dest_airport = None
        else:
            # Fallback to selectbox if no search
            default_index = 0
            if st.session_state.get('quick_to') and st.session_state.get('quick_to') in airport_options:
                default_index = airport_options.index(st.session_state.get('quick_to'))
            dest_airport = st.sidebar.selectbox("To Airport", airport_options, index=default_index, key="to_selectbox")
        
        # Show airport info if selected
        if dest_airport:
            airport_info = get_airport_info(airports_df, dest_airport)
            if airport_info:
                connected_count = get_connected_airports_count(analyzer, dest_airport)
                st.sidebar.info(f"**{airport_info['name']}**\n{airport_info['city']}, {airport_info['country']}\n{connected_count} connections")
        
        # Clear quick route state
        if 'quick_from' in st.session_state:
            del st.session_state['quick_from']
        if 'quick_to' in st.session_state:
            del st.session_state['quick_to']
        
        st.sidebar.markdown("---")
        
        # Find route button
        if source_airport and dest_airport:
            if st.sidebar.button("Find Route", type="primary", use_container_width=True):
                with st.spinner("Finding shortest route..."):
                    result = analyzer.find_shortest_path(source_airport, dest_airport)
                    st.session_state['route_result'] = result
        else:
            st.sidebar.warning("Please select both airports")
        
        # Display results
        if 'route_result' in st.session_state:
            display_shortest_path_result(st.session_state['route_result'], analyzer)
        else:
            # Show helpful message when no result
            st.info("How to use:\n1. Search or select your departure airport\n2. Search or select your destination airport\n3. Click 'Find Route' to discover the shortest path\n\nTip: Use Quick Examples above for popular routes!")
    
    elif mode == "Hub Analysis":
        st.sidebar.markdown("### Hub Analysis")
        
        # Country selection
        countries = analyzer.airports_df['country'].dropna().unique().tolist()
        countries.sort()
        countries.insert(0, "Global")
        
        selected_country = st.sidebar.selectbox("Select Country", countries)
        top_n = st.sidebar.slider("Number of Top Hubs", 5, 20, 10)
        
        # Analyze button
        if st.sidebar.button("Analyze Hubs", type="primary"):
            with st.spinner("Analyzing hubs..."):
                country_filter = None if selected_country == "Global" else selected_country
                result = analyzer.analyze_hubs(country_filter, top_n)
                st.session_state['hub_result'] = result
        
        # Display results
        if 'hub_result' in st.session_state:
            display_hub_analysis_result(st.session_state['hub_result'])
    
    elif mode == "Hub Removal What-If":
        st.sidebar.markdown("### Hub Removal Analysis")
        
        # Get available hubs
        airports_df = analyzer.airports_df
        hub_options = airports_df[airports_df['iata'].notna()]['iata'].sort_values().tolist()
        
        # Hub selection
        selected_hub = st.sidebar.selectbox("Select Hub to Remove", hub_options)
        
        # Analyze button
        if st.sidebar.button("Analyze Impact", type="primary"):
            with st.spinner("Analyzing hub removal impact..."):
                result = analyzer.hub_removal_analysis(selected_hub)
                st.session_state['removal_result'] = result
        
        # Display results
        if 'removal_result' in st.session_state:
            display_hub_removal_result(st.session_state['removal_result'])
    
    elif mode == "Network Overview":
        st.sidebar.markdown("### Network Overview")
        
        # Display network statistics
        display_network_stats(analyzer)
        
        # Global hub analysis
        st.markdown("### Global Top Hubs")
        
        if st.button("Analyze Global Hubs", type="primary"):
            with st.spinner("Analyzing global hubs..."):
                result = analyzer.analyze_hubs(None, 20)
                st.session_state['global_hub_result'] = result
        
        if 'global_hub_result' in st.session_state:
            display_hub_analysis_result(st.session_state['global_hub_result'])
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>Flight Route Advisor - Powered by NetworkX & Streamlit</p>
        <p>Data Source: OpenFlights Dataset</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()