"""
Flight Route Advisor - Streamlit Application
Google Flights inspired UI for flight route analysis
"""

import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
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


@st.cache_data(show_spinner="Loading hub data...")
def load_all_hubs_data(_analyzer: FlightGraphAnalyzer):
    """Load and cache all hubs data - this is expensive so we cache it
    
    Note: _analyzer has leading underscore so Streamlit doesn't try to hash it
    """
    import os
    from pathlib import Path
    
    # Check if pre-computed file exists
    hubs_file = Path("data/cleaned/hubs_data.csv")
    
    if hubs_file.exists():
        try:
            # Load from CSV (much faster - instant load)
            hubs_df = pd.read_csv(hubs_file)
            return hubs_df.to_dict('records')
        except Exception as e:
            # If CSV is corrupted, delete it and recompute
            hubs_file.unlink()
    
    # Compute if file doesn't exist (first time only - may take 30-60 seconds)
    # This will be cached by Streamlit, so subsequent loads are instant
    try:
        result_all = _analyzer.analyze_hubs(country=None, top_n=10000)
        if "error" not in result_all:
            hubs_data = result_all.get('all_hubs', [])
            
            # Save to CSV for future use (persistent cache)
            if hubs_data:
                os.makedirs("data/cleaned", exist_ok=True)
                hubs_df = pd.DataFrame(hubs_data)
                hubs_df.to_csv(hubs_file, index=False)
            
            return hubs_data
        return []
    except Exception as e:
        st.error(f"Error loading hubs: {str(e)}")
        return []


@st.cache_data
def get_filtered_hubs(hubs_data: List[Dict[str, Any]], country: str, size_metric: str) -> List[Dict[str, Any]]:
    """Filter and sort hubs; cached by country + size metric"""
    filtered = hubs_data
    if country and country != "All Countries":
        filtered = [h for h in hubs_data if h.get('country', '') == country]
    # Sort by degree centrality (primary) and betweenness (secondary) for stability
    filtered = sorted(
        filtered,
        key=lambda x: (x.get('degree_centrality', 0), x.get('betweenness_centrality', 0)),
        reverse=True
    )
    return filtered


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


def create_interactive_map(
    hubs_data: List[Dict[str, Any]], 
    analyzer: FlightGraphAnalyzer,
    size_metric: str = "degree_centrality",
    selected_from: str = None,
    selected_to: str = None,
    route_path: List[str] = None,
    route_coords: List[Tuple[float, float]] = None
) -> folium.Map:
    """Create interactive map with hubs and/or route visualization"""
    try:
        # Get coordinates for all hubs (can be empty if we want to hide hubs)
        hub_coords = _get_hub_coordinates(hubs_data, analyzer) if hubs_data else []

        # If no hubs and no route, nothing to show
        if not hub_coords and not route_coords:
            return None
        
        # Calculate center and zoom (prefers route when available)
        center_lat, center_lon, zoom_start = _calculate_map_center(hub_coords, route_coords)
        
        # Create map with error handling
        try:
            m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_start)
        except Exception:
            m = folium.Map(location=[20, 0], zoom_start=2)
        
        # Add route line if available
        _add_route_line(m, route_coords, route_path)
            
        # Add hub markers if we have hubs
        if hub_coords:
            _add_hub_markers(m, hub_coords, size_metric, selected_from, selected_to, route_path)
        
        return m
    except Exception:
        return None


def _add_route_line(
    map_obj: folium.Map,
    route_coords: List[Tuple[float, float]] = None,
    route_path: List[str] = None
) -> None:
    """Add route line and plane icons to the map if valid coordinates are provided"""
    if not route_coords or len(route_coords) < 2:
        return
    
    try:
        valid_route_coords = [(lat, lon) for lat, lon in route_coords 
                             if isinstance(lat, (int, float)) and isinstance(lon, (int, float))
                             and -90 <= lat <= 90 and -180 <= lon <= 180]
        if len(valid_route_coords) > 1:
            folium.PolyLine(
                valid_route_coords,
                color="#1a73e8",
                weight=4,
                opacity=0.8,
                popup="Flight Route"
            ).add_to(map_obj)

            # Add plane icons at each stop (start/stop colored)
            for idx, (lat, lon) in enumerate(valid_route_coords):
                label = None
                if route_path and idx < len(route_path):
                    label = route_path[idx]
                else:
                    label = f"Stop {idx+1}"

                if idx == 0:
                    color = "green"
                elif idx == len(valid_route_coords) - 1:
                    color = "red"
                else:
                    color = "blue"

                try:
                    folium.Marker(
                        location=[lat, lon],
                        popup=label,
                        tooltip=label,
                        icon=folium.Icon(color=color, icon="plane", prefix="fa")
                    ).add_to(map_obj)
                except Exception:
                    continue
    except Exception:
        # Skip route line if there's an error
        pass


def _render_main_map(
    analyzer: FlightGraphAnalyzer,
    filtered_hubs: List[Dict[str, Any]],
    size_metric: str,
    from_airport: str,
    to_airport: str
) -> None:
    """Render the hubs map (no route overlay)"""
    st.markdown("### 🌍 Hubs Map")
    
    # Always show hubs; no route overlay here
    try:
        interactive_map = create_interactive_map(
            hubs_data=filtered_hubs,
            analyzer=analyzer,
            size_metric=size_metric,
            selected_from=from_airport,
            selected_to=to_airport,
            route_path=None,
            route_coords=None
        )
        
        if interactive_map is not None:
            map_key = f"hubs_map_{len(filtered_hubs)}_{size_metric}"
            st_folium(interactive_map, width=1200, height=650, key=map_key)
        else:
            st.error("Failed to create hubs map.")
    except Exception as e:
        st.error(f"Error creating hubs map: {str(e)}")
        try:
            fallback_map = folium.Map(location=[20, 0], zoom_start=2)
            st_folium(fallback_map, width=1200, height=650, key="hubs_fallback_map")
        except:
            pass


def _render_route_map(analyzer: FlightGraphAnalyzer) -> None:
    """Render a separate map for the main route (if any)"""
    if 'route_result' not in st.session_state:
        return
    result = st.session_state['route_result']
    if "error" in result:
        return
    route_path = result.get('path', [])
    path_coordinates = analyzer.get_airport_coordinates(route_path)
    if not path_coordinates:
        return
    route_coords = [(lat, lon) for lat, lon, _ in path_coordinates]
        
    st.markdown("### ✈️ Route Map")
    try:
        route_map = create_interactive_map(
            hubs_data=[],  # no hubs to avoid clutter
            analyzer=analyzer,
            size_metric="degree_centrality",
            selected_from=route_path[0] if route_path else None,
            selected_to=route_path[-1] if route_path else None,
            route_path=route_path,
            route_coords=route_coords
        )
        if route_map:
            st_folium(route_map, width=1200, height=650, key="route_only_map")
    except Exception as e:
        st.error(f"Error rendering route map: {str(e)}")


def _add_hub_markers(
    map_obj: folium.Map,
    hub_coords: List[Dict[str, Any]],
    size_metric: str,
    selected_from: str = None,
    selected_to: str = None,
    route_path: List[str] = None
) -> None:
    """Add hub markers to the map with size and color based on centrality and selection"""
    try:
        if size_metric == "degree_centrality":
            values = [h['degree'] for h in hub_coords]
        else:
            values = [h['betweenness'] for h in hub_coords]
        
        if not values:
            return
    
        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val if max_val > min_val else 1

        # Cluster markers to improve map performance with many hubs
        cluster = MarkerCluster()
        cluster.add_to(map_obj)
        
        for hub in hub_coords:
            try:
                # Calculate radius based on centrality
                centrality = hub['degree'] if size_metric == "degree_centrality" else hub['betweenness']
                radius = max(5, min(30, 5 + (centrality - min_val) / range_val * 25)) if range_val > 0 else 15
                
                # Determine color based on selection
                if hub['iata'] == selected_from:
                    color = fill_color = '#34a853'  # Green for source
                elif hub['iata'] == selected_to:
                    color = fill_color = '#ea4335'  # Red for destination
                elif route_path and hub['iata'] in route_path:
                    color = fill_color = '#1a73e8'  # Blue for route stops
                else:
                    color = fill_color = '#5f6368'  # Gray for other hubs
                
                # Create popup text
                popup_text = f"""
                <div style="min-width: 200px;">
                    <b>{hub['iata']}</b><br>
                    {hub['name']}<br>
                    {hub['city']}, {hub['country']}<br>
                    <hr>
                    <b>Centrality:</b><br>
                    Degree: {hub['degree']:.4f}<br>
                    Betweenness: {hub['betweenness']:.4f}<br>
                    <hr>
                    <small>Click to select as From/To</small>
                </div>
                """
                
                # Add circle marker
                folium.CircleMarker(
                    location=[hub['lat'], hub['lon']],
                    radius=radius,
                    popup=folium.Popup(popup_text, max_width=250),
                    tooltip=f"{hub['iata']} - {hub['name']}",
                    color=color,
                    fill=True,
                    fillColor=fill_color,
                    fillOpacity=0.7,
                    weight=3
                ).add_to(cluster)
            except Exception:
                # Skip invalid hub markers
                continue
    except Exception:
        # If marker creation fails, silently continue
        pass


def _get_hub_coordinates(hubs_data: List[Dict[str, Any]], analyzer: FlightGraphAnalyzer) -> List[Dict[str, Any]]:
    """Extract and validate hub coordinates from hubs data"""
    hub_coords = []
    for hub in hubs_data:
        try:
            iata = hub.get('airport')
            if iata:
                coords = analyzer.get_airport_coordinates([iata])
                if coords and len(coords) > 0:
                    lat, lon, _ = coords[0]
                    # Validate coordinates
                    if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
                        if -90 <= lat <= 90 and -180 <= lon <= 180:
                            hub_coords.append({
                                'lat': float(lat),
                                'lon': float(lon),
                                'iata': iata,
                                'name': hub.get('name', ''),
                                'city': hub.get('city', ''),
                                'country': hub.get('country', ''),
                                'degree': float(hub.get('degree_centrality', 0)),
                                'betweenness': float(hub.get('betweenness_centrality', 0))
                            })
        except Exception:
            # Skip invalid hubs
            continue
    return hub_coords


def _calculate_map_center(hub_coords: List[Dict[str, Any]], route_coords: List[Tuple[float, float]] = None) -> Tuple[float, float, int]:
    """Calculate map center and zoom level"""
    try:
        if route_coords and len(route_coords) > 0:
            valid_route_coords = [(lat, lon) for lat, lon in route_coords 
                                 if isinstance(lat, (int, float)) and isinstance(lon, (int, float))
                                 and -90 <= lat <= 90 and -180 <= lon <= 180]
            if valid_route_coords:
                center_lat = sum(coord[0] for coord in valid_route_coords) / len(valid_route_coords)
                center_lon = sum(coord[1] for coord in valid_route_coords) / len(valid_route_coords)
                zoom_start = 4
            else:
                raise ValueError("No valid route coordinates")
        else:
            center_lat = sum(h['lat'] for h in hub_coords) / len(hub_coords)
            center_lon = sum(h['lon'] for h in hub_coords) / len(hub_coords)
            zoom_start = 2
        
        # Validate center coordinates
        if not (-90 <= center_lat <= 90 and -180 <= center_lon <= 180):
            return 20.0, 0.0, 2
        
        return center_lat, center_lon, zoom_start
    except Exception:
        # Fallback to default center
        return 20.0, 0.0, 2


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


def _render_sidebar(analyzer: FlightGraphAnalyzer, all_hubs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Render sidebar with search controls (route only)"""
    st.markdown("### 🔍 Search & Filter")
    
    # Airport selection
    airports_df = analyzer.airports_df
    airport_df = airports_df[airports_df['iata'].notna()].copy().sort_values(by='iata')
    airport_options = airport_df['iata'].tolist()
    airport_labels = get_airport_display_map(airports_df)
    
    from_airport = st.selectbox(
        "From",
        airport_options,
        key='from',
        format_func=lambda x: airport_labels.get(x, x)
    )
    
    to_airport = st.selectbox(
        "To",
        airport_options,
        key='to',
        format_func=lambda x: airport_labels.get(x, x)
    )
    
    max_stops = st.selectbox(
        "Max stops (transits)",
        options=[0, 1, 2],
        index=st.session_state.get('max_stops', 2),
        help="Limit number of transit points"
    )
    
    compute_alt_routes = st.checkbox("Show alternative routes", value=False)
    
    search_clicked = st.button("🔍 Search Route", type="primary", use_container_width=True)

    return {
        'from_airport': from_airport,
        'to_airport': to_airport,
        'max_stops': max_stops,
        'compute_alt_routes': compute_alt_routes,
        'search_clicked': search_clicked,
    }


def _render_map_controls(all_hubs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Render map controls (separate from Search & Filter)"""
    st.markdown("### 🗺️ Map Controls")
    
    size_metric = st.selectbox(
        "Point size based on",
        ["degree_centrality", "betweenness_centrality"],
        index=0,
        help="Larger points = more important hubs"
    )
    
    # Country filter
    countries = sorted(set(h.get('country', '') for h in all_hubs if h.get('country')))
    country_options = ["All Countries"] + countries
    selected_country = st.selectbox("Filter by Country", country_options)

    apply_map = st.button("Apply map filters", type="secondary")
    
    return {
        'size_metric': size_metric,
        'selected_country': selected_country,
        'apply_map': apply_map
    }


def _search_route(analyzer: FlightGraphAnalyzer, search_params: Dict[str, Any]) -> None:
    """Perform route search and store results in session state"""
    from_airport = search_params['from_airport']
    to_airport = search_params['to_airport']
    max_stops = search_params['max_stops']
    compute_alt_routes = search_params['compute_alt_routes']
    
    with st.spinner("Finding route..."):
        # Main route
        main_result = analyzer.find_optimized_route(
            from_airport, to_airport, objective="distance", max_stops=max_stops
        )
        if ("error" in main_result) or (main_result.get("stops") != max_stops):
            main_result = {"error": f"No route found with exactly {max_stops} transit(s)"}
    
    # Alternative paths
        if compute_alt_routes:
            # For max_stops = 0, still allow alternative routes with stops (1-2)
            alt_search_stops = None if max_stops == 0 else max_stops
            alt_paths_raw = analyzer.find_robust_transfer_paths(
                from_airport, to_airport, k=3, max_stops=alt_search_stops
            )
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
                "paths": alt_filtered[:3],
                "total_paths_found": len(alt_filtered)
            }
            if not alt_filtered:
                alt_paths = {"error": "No alternative routes available."}
        else:
            alt_paths = {"error": "Alternative routes not computed."}
        
        st.session_state['route_result'] = main_result
        st.session_state['alt_paths'] = alt_paths
        st.session_state.pop('alt_hubs', None)


def main():
    """Main Streamlit application - Interactive Map Centered"""
    
    st.markdown('<h1 class="main-header">Flight Route Advisor</h1>', unsafe_allow_html=True)
    
    # Load data
    with st.spinner("Loading flight network..."):
        analyzer = load_data()
    
    if analyzer is None:
        st.error("Failed to load data. Please run notebook/flight_route.ipynb first.")
        return
    
    # Load all hubs data (cached)
    all_hubs = load_all_hubs_data(_analyzer=analyzer)
    
    if not all_hubs:
        st.warning("No hub data available. Please check if data files exist.")
        st.stop()
    
    # Sidebar for controls
    with st.sidebar:
        sidebar_result = _render_sidebar(analyzer, all_hubs)
        
        # Handle route search
        if sidebar_result and sidebar_result.get('search_clicked'):
            _search_route(analyzer, sidebar_result)
    
        # Map controls (separate from search but still in sidebar)
        map_ctrl = _render_map_controls(all_hubs)
        if map_ctrl.get('apply_map'):
            st.session_state['applied_size_metric'] = map_ctrl.get('size_metric', st.session_state['applied_size_metric'])
            st.session_state['applied_country'] = map_ctrl.get('selected_country', st.session_state['applied_country'])
            # Clear current route results to avoid overlap when applying map filters
            st.session_state.pop('route_result', None)
            st.session_state.pop('alt_paths', None)
            st.session_state['map_applied'] = True
        # If no apply yet, ensure default flag
        if 'map_applied' not in st.session_state:
            st.session_state['map_applied'] = False
    
    # Defaults for applied map settings
    if 'applied_size_metric' not in st.session_state:
        st.session_state['applied_size_metric'] = 'degree_centrality'
    if 'applied_country' not in st.session_state:
        st.session_state['applied_country'] = "All Countries"

    # Extract search values with safe defaults
    if sidebar_result:
        from_airport = sidebar_result.get('from_airport', '')
        to_airport = sidebar_result.get('to_airport', '')
    else:
        from_airport = ''
        to_airport = ''

    size_metric = st.session_state['applied_size_metric']
    applied_country = st.session_state['applied_country']
    map_applied = st.session_state.get('map_applied', False)

    # Detect if we just ran a search in this rerun
    is_search_rerun = st.session_state.get('route_result') is not None and sidebar_result and sidebar_result.get('search_clicked')

    # Filter hubs using applied settings (cached) only when applied at least once
    # Skip hubs render on the rerun triggered by Search to speed things up
    if map_applied:
        filtered_hubs = get_filtered_hubs(all_hubs, applied_country, size_metric)
        if not is_search_rerun:
            st.info(f"Showing {len(filtered_hubs)} hubs on map (Country: {applied_country}, Size metric: {size_metric})")
            _render_main_map(analyzer, filtered_hubs, size_metric, from_airport, to_airport)
        else:
            st.info("Hubs map skipped during search to speed up. Re-apply map filters to view hubs.")
    else:
        filtered_hubs = []
        st.info("Apply map filters to load hubs map.")
    
    # Route map (separate from hubs)
    _render_route_map(analyzer)
    
    # Display route details below map
    _render_route_details(analyzer)
    
    # Network Statistics (collapsed; show only Airports, Routes, Density)
    stats_expander = st.expander("📊 Network Statistics", expanded=False)
    with stats_expander:
        stats = analyzer.get_network_stats()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Airports", f"{stats['total_nodes']:,}")
        with col2:
            st.metric("Routes", f"{stats['total_edges']:,}")
        with col3:
            st.metric("Density", f"{stats['density']:.4f}")
    

def _render_route_details(analyzer: FlightGraphAnalyzer) -> None:
    """Render route details and alternative routes"""
    if 'route_result' not in st.session_state:
        return
    
    result = st.session_state['route_result']
    if "error" not in result:
        st.markdown("---")
        st.markdown("### ✈️ Route Details")
        
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
        
        # Route legs
        with st.expander("Route Legs", expanded=False):
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
                
                if i < len(result['legs']) and i <= len(transit_times):
                    transit_hours = int(transit_times[i-1])
                    transit_mins = int((transit_times[i-1] - transit_hours) * 60)
                    st.markdown(f"  ⏱️ Transit at {leg['to']}: {transit_hours}h {transit_mins}m")
    else:
        # Show message when no main route found
        st.warning(result.get("error", "No route found with current constraints."))
    
    # Alternative routes
    if 'alt_paths' in st.session_state:
        alt_paths = st.session_state['alt_paths']
        if "error" not in alt_paths and alt_paths.get('paths'):
            st.markdown("---")
            st.markdown("### 🔄 Alternative Routes")
            for i, path_info in enumerate(alt_paths['paths'][:2], 1):
                title = f"Option {i}: {' → '.join(path_info['path'])} ({path_info['stops']} stops, {path_info['distance_km']:,.0f} km"
                if path_info.get('total_route_time_hours'):
                    total_hours = int(path_info['total_route_time_hours'])
                    total_mins = int((path_info['total_route_time_hours'] - total_hours) * 60)
                    title += f", {total_hours}h {total_mins}m"
                title += ")"
                st.markdown(title)

                # Show map for each alternative route (no hubs to avoid clutter)
                try:
                    alt_path = path_info.get('path', [])
                    path_coordinates = analyzer.get_airport_coordinates(alt_path)
                    if path_coordinates:
                        alt_route_coords = [(lat, lon) for lat, lon, _ in path_coordinates]
                        alt_map = create_interactive_map(
                            hubs_data=[],
                            analyzer=analyzer,
                            size_metric="degree_centrality",
                            selected_from=alt_path[0] if alt_path else None,
                            selected_to=alt_path[-1] if alt_path else None,
                            route_path=alt_path,
                            route_coords=alt_route_coords
                        )
                        if alt_map:
                            st_folium(alt_map, width=1000, height=550, key=f"alt_route_map_{i}")
                except Exception:
                    pass
        elif alt_paths.get("error"):
            st.info(alt_paths.get("error"))


if __name__ == "__main__":
    main()
