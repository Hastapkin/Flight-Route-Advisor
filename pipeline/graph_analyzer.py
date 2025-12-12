"""
Graph Analyzer for Flight Route Analysis
Handles NetworkX graph operations, shortest path, and hub analysis
"""

import networkx as nx
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import json
from .flight_time import compute_total_route_time


class FlightGraphAnalyzer:
    """Analyzes flight networks using NetworkX graphs"""
    
    def __init__(self, airports_df: pd.DataFrame, routes_df: pd.DataFrame):
        """
        Initialize with cleaned airports and routes data
        
        Args:
            airports_df: Cleaned airports DataFrame
            routes_df: Cleaned routes DataFrame with distance_km
        """
        self.airports_df = airports_df
        self.routes_df = routes_df
        self.graph = None
        self._build_graph()
    
    def _build_graph(self) -> None:
        """Build NetworkX graph from routes and airports data"""
        print("Building flight network graph...")
        
        # Create directed graph (flights have direction)
        self.graph = nx.DiGraph()
        
        # Add airport nodes
        for _, airport in self.airports_df.iterrows():
            self.graph.add_node(
                airport['airport_id'],
                iata=airport.get('iata', ''),
                name=airport.get('name', ''),
                city=airport.get('city', ''),
                country=airport.get('country', ''),
                latitude=float(airport.get('latitude', 0)),
                longitude=float(airport.get('longitude', 0))
            )
        
        # Add route edges
        edge_count = 0
        for _, route in self.routes_df.iterrows():
            if pd.notna(route.get('distance_km')):
                self.graph.add_edge(
                    route['source_airport_id'],
                    route['destination_airport_id'],
                    weight=float(route['distance_km']),
                    distance_km=float(route['distance_km']),
                    airline=str(route.get('airline', '')).upper(),
                    airline_id=int(route.get('airline_id', 0)) if pd.notna(route.get('airline_id')) else 0,
                    stops=int(route.get('stops', 0)) if pd.notna(route.get('stops')) else 0
                )
                edge_count += 1
        
        print(f"Graph built: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
    
    def find_shortest_path(self, source_iata: str, dest_iata: str) -> Dict[str, Any]:
        """
        Find shortest path between two airports using Dijkstra algorithm
        
        Args:
            source_iata: Source airport IATA code (e.g., 'SGN')
            dest_iata: Destination airport IATA code (e.g., 'LHR')
            
        Returns:
            Dictionary with path information
        """
        # Find airport IDs from IATA codes
        source_id = self._get_airport_id_by_iata(source_iata)
        dest_id = self._get_airport_id_by_iata(dest_iata)
        
        if not source_id or not dest_id:
            return {"error": "Airport not found"}
        
        if source_id == dest_id:
            return {"error": "Source and destination are the same"}
        
        return self.find_optimized_route(
            source_iata,
            dest_iata,
            objective="distance",
            preferences={}
        )

    def find_optimized_route(
        self,
        source_iata: str,
        dest_iata: str,
        objective: str = "distance",
        preferences: Optional[Dict[str, Any]] = None,
        max_stops: Optional[int] = 2,
    ) -> Dict[str, Any]:
        """
        Find routes using multiple optimization criteria.

        Args:
            source_iata: Source airport code
            dest_iata: Destination airport code
            objective: Optimization objective ('distance' or 'transfers')
            preferences: Constraints (avoid_countries, allowed_countries, preferred_airlines)
        """
        preferences = preferences or {}

        source_id = self._get_airport_id_by_iata(source_iata)
        dest_id = self._get_airport_id_by_iata(dest_iata)

        if not source_id or not dest_id:
            return {"error": "Airport not found"}

        if source_id == dest_id:
            return {"error": "Source and destination are the same"}

        working_graph = self.graph.copy()
        self._apply_preferences(working_graph, source_id, dest_id, preferences)

        try:
            # Choose algorithm based on objective
            if objective == "transfers":
                path_nodes = nx.shortest_path(working_graph, source_id, dest_id)
                total_distance = self._calculate_path_distance(path_nodes)
            else:
                # Fast path when max_stops is small (common case: 0-2)
                if max_stops is not None and max_stops <= 2:
                    path_nodes = self._fast_constrained_path(
                        working_graph, source_id, dest_id, max_stops=max_stops
                    )
                    if path_nodes is None:
                        return {"error": f"No path found within {max_stops} stops"}
                    total_distance = self._calculate_path_weight(working_graph, path_nodes)
                elif max_stops is not None:
                    # Fallback to simple paths enumeration with limit
                    path_nodes = self._find_path_with_stop_limit(
                        working_graph, source_id, dest_id, max_stops=max_stops
                    )
                    if path_nodes is None:
                        return {"error": f"No path found within {max_stops} stops"}
                    total_distance = self._calculate_path_weight(working_graph, path_nodes)
                else:
                    path_nodes = nx.shortest_path(
                        working_graph,
                        source_id,
                        dest_id,
                        weight='weight'
                    )
                    total_distance = nx.shortest_path_length(
                        working_graph,
                        source_id,
                        dest_id,
                        weight='weight'
                    )

            path_iata = [self._get_iata_by_airport_id(node) for node in path_nodes]
            legs = []

            for i in range(len(path_nodes) - 1):
                edge_data = self.graph[path_nodes[i]][path_nodes[i+1]]
                legs.append({
                    "from": path_iata[i],
                    "to": path_iata[i+1],
                    "distance_km": edge_data.get('distance_km', 0),
                    "airline": edge_data.get('airline', ''),
                    "stops": edge_data.get('stops', 0)
                })

            # Calculate flight time for the route
            time_info = compute_total_route_time(legs, use_random_transit=True)
            
            summary = self._build_criteria_summary(objective, preferences, len(path_nodes) - 2)

            result = {
                "source": source_iata,
                "destination": dest_iata,
                "path": path_iata,
                "total_distance_km": total_distance,
                "legs": legs,
                "stops": len(path_nodes) - 2,
                "objective": objective,
                "criteria_summary": summary
            }
            
            # Add flight time information if available
            if time_info:
                result.update({
                    "total_flight_time_hours": time_info.get('total_flight_time_hours'),
                    "total_transit_time_hours": time_info.get('total_transit_time_hours'),
                    "total_route_time_hours": time_info.get('total_route_time_hours'),
                    "leg_times": time_info.get('leg_times', []),
                    "transit_times": time_info.get('transit_times', [])
                })
            
            return result

        except nx.NetworkXNoPath:
            return {"error": "No path found with current constraints"}
        except Exception as e:
            return {"error": f"Error finding route: {str(e)}"}

    def _calculate_path_weight(self, graph: nx.DiGraph, path_nodes: List[int]) -> float:
        """Sum weights along a path safely."""
        total = 0.0
        for i in range(len(path_nodes) - 1):
            edge_data = graph[path_nodes[i]][path_nodes[i + 1]]
            total += float(edge_data.get("weight", edge_data.get("distance_km", 0)))
        return total

    def _fast_constrained_path(
        self,
        graph: nx.DiGraph,
        source_id: int,
        dest_id: int,
        max_stops: int,
    ) -> Optional[List[int]]:
        """
        Fast path finder for small stop limits (0-2) using direct enumeration,
        avoiding expensive k-shortest simple paths.
        """
        # 0 stops: direct edge
        if max_stops == 0:
            if graph.has_edge(source_id, dest_id):
                return [source_id, dest_id]
            return None

        # Pre-fetch neighbors for speed
        neigh = graph.adj

        # 1 stop: source -> mid -> dest
        if max_stops == 1:
            best = None
            best_w = float("inf")
            for mid in neigh[source_id]:
                if mid == dest_id:
                    return [source_id, dest_id]
                if graph.has_edge(mid, dest_id):
                    w = (
                        float(graph[source_id][mid].get("weight", 0))
                        + float(graph[mid][dest_id].get("weight", 0))
                    )
                    if w < best_w:
                        best_w = w
                        best = [source_id, mid, dest_id]
            return best

        # 2 stops: source -> m1 -> m2 -> dest
        best = None
        best_w = float("inf")
        for m1 in neigh[source_id]:
            if m1 == dest_id:
                return [source_id, dest_id]
            w1 = float(graph[source_id][m1].get("weight", 0))
            for m2 in neigh[m1]:
                if m2 == source_id:
                    continue
                w2 = w1 + float(graph[m1][m2].get("weight", 0))
                if m2 == dest_id:
                    if w2 < best_w:
                        best_w = w2
                        best = [source_id, m1, dest_id]
                    continue
                if graph.has_edge(m2, dest_id):
                    w = w2 + float(graph[m2][dest_id].get("weight", 0))
                    if w < best_w:
                        best_w = w
                        best = [source_id, m1, m2, dest_id]
        return best

    def _find_path_with_stop_limit(
        self,
        graph: nx.DiGraph,
        source_id: int,
        dest_id: int,
        max_stops: int,
        max_paths: int = 30,
    ) -> Optional[List[int]]:
        """
        Find a path that satisfies a maximum number of stops (nodes between ends).
        Uses k-shortest simple paths enumeration and returns the first that fits.
        """
        try:
            for idx, path in enumerate(
                nx.shortest_simple_paths(graph, source_id, dest_id, weight="weight")
            ):
                if len(path) - 2 <= max_stops:
                    return path
                if idx >= max_paths:
                    break
        except nx.NetworkXNoPath:
            return None
        return None

    def _apply_preferences(
        self,
        graph: nx.DiGraph,
        source_id: int,
        dest_id: int,
        preferences: Dict[str, Any]
    ) -> None:
        """Apply airline and country constraints to a working graph."""
        avoid_countries = {
            country.lower()
            for country in preferences.get("avoid_countries", [])
            if country
        }
        allowed_countries = {
            country.lower()
            for country in preferences.get("allowed_countries", [])
            if country
        }
        preferred_airlines = {
            airline.upper()
            for airline in preferences.get("preferred_airlines", [])
            if airline
        }

        if avoid_countries or allowed_countries:
            nodes_to_remove = []
            for node, data in graph.nodes(data=True):
                if node in (source_id, dest_id):
                    continue
                country = str(data.get("country", "")).lower()

                if allowed_countries and country not in allowed_countries:
                    nodes_to_remove.append(node)
                elif avoid_countries and country in avoid_countries:
                    nodes_to_remove.append(node)

            graph.remove_nodes_from(nodes_to_remove)

        if preferred_airlines:
            edges_to_remove = []
            for u, v, data in graph.edges(data=True):
                airline = str(data.get("airline", "")).upper()
                if airline and airline not in preferred_airlines:
                    edges_to_remove.append((u, v))
            graph.remove_edges_from(edges_to_remove)

    def _calculate_path_distance(self, path_nodes: List[int]) -> float:
        """Calculate distance for an unweighted path."""
        distance = 0.0
        for i in range(len(path_nodes) - 1):
            edge_data = self.graph[path_nodes[i]][path_nodes[i + 1]]
            distance += edge_data.get('distance_km', 0)
        return distance

    def _build_criteria_summary(
        self,
        objective: str,
        preferences: Dict[str, Any],
        transfers: int
    ) -> Dict[str, Any]:
        """Create a structured summary describing applied criteria."""
        summary = {
            "objective": "Shortest Distance" if objective == "distance" else "Fewest Transfers",
            "transfers": transfers,
            "notes": []
        }

        if preferences.get("preferred_airlines"):
            summary["notes"].append(
                f"Airlines restricted to: {', '.join(preferences['preferred_airlines'])}"
            )

        if preferences.get("avoid_countries"):
            summary["notes"].append(
                f"Avoided transit countries: {', '.join(preferences['avoid_countries'])}"
            )

        if preferences.get("allowed_countries"):
            summary["notes"].append(
                f"Transit limited to: {', '.join(preferences['allowed_countries'])}"
            )

        return summary
    
    def analyze_hubs(self, country: str = None, top_n: int = 10) -> Dict[str, Any]:
        """
        Analyze airport hubs using centrality measures
        
        Args:
            country: Filter by country (optional)
            top_n: Number of top hubs to return
            
        Returns:
            Dictionary with hub analysis results
        """
        if not self.graph:
            return {"error": "Graph not built"}
        
        # Calculate centrality measures
        degree_centrality = nx.degree_centrality(self.graph)
        betweenness_centrality = nx.betweenness_centrality(self.graph, weight='weight')
        closeness_centrality = nx.closeness_centrality(self.graph, distance='weight')
        pagerank = nx.pagerank(self.graph, weight='weight')
        
        # Create hub data
        hubs_data = []
        for node in self.graph.nodes():
            airport_info = self._get_airport_info(node)
            if airport_info:
                hub_info = {
                    "airport": airport_info['iata'],
                    "name": airport_info['name'],
                    "city": airport_info['city'],
                    "country": airport_info['country'],
                    "degree_centrality": degree_centrality.get(node, 0),
                    "betweenness_centrality": betweenness_centrality.get(node, 0),
                    "closeness_centrality": closeness_centrality.get(node, 0),
                    "pagerank": pagerank.get(node, 0)
                }
                
                # Filter by country if specified
                if not country or airport_info['country'].lower() == country.lower():
                    hubs_data.append(hub_info)
        
        # Sort by degree centrality
        hubs_data.sort(key=lambda x: x['degree_centrality'], reverse=True)
        
        # Get top hubs and backup hubs
        top_hubs = hubs_data[:top_n]
        backup_hubs = hubs_data[top_n:top_n*2] if len(hubs_data) > top_n else []
        
        return {
            "country": country or "Global",
            "top_hubs": top_hubs,
            "backup_hubs": backup_hubs,
            "total_airports": len(hubs_data)
        }
    
    def get_network_stats(self) -> Dict[str, Any]:
        """Get basic network statistics"""
        if not self.graph:
            return {"error": "Graph not built"}
        
        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "density": nx.density(self.graph),
            "is_strongly_connected": nx.is_strongly_connected(self.graph),
            "is_weakly_connected": nx.is_weakly_connected(self.graph),
            "number_of_strongly_connected_components": nx.number_strongly_connected_components(self.graph),
            "number_of_weakly_connected_components": nx.number_weakly_connected_components(self.graph)
        }
    
    def hub_removal_analysis(self, hub_iata: str) -> Dict[str, Any]:
        """
        Analyze network impact when removing a specific hub (what-if analysis)
        
        Args:
            hub_iata: IATA code of hub to remove
            
        Returns:
            Dictionary with impact analysis results
        """
        if not self.graph:
            return {"error": "Graph not built"}
        
        # Find hub airport ID
        hub_id = self._get_airport_id_by_iata(hub_iata)
        if not hub_id:
            return {"error": f"Hub {hub_iata} not found"}
        
        if hub_id not in self.graph.nodes():
            return {"error": f"Hub {hub_iata} not in network"}
        
        # Get original network stats
        original_stats = self.get_network_stats()
        
        # Create copy of graph without the hub
        graph_without_hub = self.graph.copy()
        graph_without_hub.remove_node(hub_id)
        
        # Get network stats after hub removal
        remaining_stats = {
            "total_nodes": graph_without_hub.number_of_nodes(),
            "total_edges": graph_without_hub.number_of_edges(),
            "density": nx.density(graph_without_hub),
            "is_strongly_connected": nx.is_strongly_connected(graph_without_hub),
            "is_weakly_connected": nx.is_weakly_connected(graph_without_hub),
            "number_of_strongly_connected_components": nx.number_strongly_connected_components(graph_without_hub),
            "number_of_weakly_connected_components": nx.number_weakly_connected_components(graph_without_hub)
        }
        
        # Calculate impact metrics
        impact_metrics = {
            "nodes_lost": original_stats['total_nodes'] - remaining_stats['total_nodes'],
            "edges_lost": original_stats['total_edges'] - remaining_stats['total_edges'],
            "density_change": remaining_stats['density'] - original_stats['density'],
            "connectivity_broken": original_stats['is_strongly_connected'] and not remaining_stats['is_strongly_connected'],
            "components_increase": remaining_stats['number_of_strongly_connected_components'] - original_stats['number_of_strongly_connected_components']
        }
        
        # Find affected routes (routes that used this hub)
        affected_routes = []
        hub_info = self._get_airport_info(hub_id)
        
        for _, route in self.routes_df.iterrows():
            if (route['source_airport_id'] == hub_id or route['destination_airport_id'] == hub_id):
                source_iata = self._get_iata_by_airport_id(route['source_airport_id'])
                dest_iata = self._get_iata_by_airport_id(route['destination_airport_id'])
                affected_routes.append({
                    "from": source_iata,
                    "to": dest_iata,
                    "distance_km": route.get('distance_km', 0)
                })
        
        # Find alternative paths for some key routes
        alternative_paths = self._find_alternative_paths(hub_id, graph_without_hub)
        
        return {
            "hub_removed": hub_iata,
            "hub_info": hub_info,
            "original_stats": original_stats,
            "remaining_stats": remaining_stats,
            "impact_metrics": impact_metrics,
            "affected_routes_count": len(affected_routes),
            "affected_routes": affected_routes[:10],  # Show first 10
            "alternative_paths": alternative_paths,
            "severity": self._assess_removal_severity(impact_metrics)
        }
    
    def _find_alternative_paths(self, removed_hub_id: int, graph_without_hub: nx.DiGraph) -> List[Dict[str, Any]]:
        """Find alternative paths for routes that were affected by hub removal"""
        alternatives = []
        
        # Get some sample routes that used the removed hub
        sample_routes = []
        for _, route in self.routes_df.iterrows():
            if (route['source_airport_id'] == removed_hub_id or 
                route['destination_airport_id'] == removed_hub_id):
                if route['source_airport_id'] != removed_hub_id:
                    sample_routes.append((route['source_airport_id'], removed_hub_id))
                if route['destination_airport_id'] != removed_hub_id:
                    sample_routes.append((removed_hub_id, route['destination_airport_id']))
        
        # Test alternative paths for a few sample routes
        for i, (source_id, dest_id) in enumerate(sample_routes[:5]):  # Test first 5
            try:
                if source_id in graph_without_hub.nodes() and dest_id in graph_without_hub.nodes():
                    alt_path = nx.shortest_path(graph_without_hub, source_id, dest_id, weight='weight')
                    alt_distance = nx.shortest_path_length(graph_without_hub, source_id, dest_id, weight='weight')
                    
                    alternatives.append({
                        "original_from": self._get_iata_by_airport_id(source_id),
                        "original_to": self._get_iata_by_airport_id(dest_id),
                        "alternative_path": [self._get_iata_by_airport_id(node) for node in alt_path],
                        "alternative_distance": alt_distance,
                        "path_length": len(alt_path) - 1
                    })
            except nx.NetworkXNoPath:
                alternatives.append({
                    "original_from": self._get_iata_by_airport_id(source_id),
                    "original_to": self._get_iata_by_airport_id(dest_id),
                    "alternative_path": "NO_ALTERNATIVE",
                    "alternative_distance": float('inf'),
                    "path_length": 0
                })
        
        return alternatives
    
    def _assess_removal_severity(self, impact_metrics: Dict[str, Any]) -> str:
        """Assess the severity of hub removal impact"""
        if impact_metrics['connectivity_broken']:
            return "CRITICAL"
        elif impact_metrics['components_increase'] > 5:
            return "HIGH"
        elif impact_metrics['edges_lost'] > 100:
            return "MEDIUM"
        else:
            return "LOW"
    
    def find_robust_transfer_paths(
        self,
        source_iata: str,
        dest_iata: str,
        k: int = 2,
        preferences: Optional[Dict[str, Any]] = None,
        max_stops: Optional[int] = 2,
    ) -> Dict[str, Any]:
        """
        Find multiple robust alternative transfer paths (k-shortest paths)
        This addresses the goal: "Suggest robust transfer paths"
        
        Args:
            source_iata: Source airport code
            dest_iata: Destination airport code
            k: Number of alternative paths to find
            preferences: Constraints (avoid_countries, allowed_countries, preferred_airlines)
            
        Returns:
            Dictionary with multiple alternative paths
        """
        preferences = preferences or {}
        
        source_id = self._get_airport_id_by_iata(source_iata)
        dest_id = self._get_airport_id_by_iata(dest_iata)
        
        if not source_id or not dest_id:
            return {"error": "Airport not found"}
        
        if source_id == dest_id:
            return {"error": "Source and destination are the same"}
        
        working_graph = self.graph.copy()
        self._apply_preferences(working_graph, source_id, dest_id, preferences)
        
        try:
            # Find k-shortest paths using NetworkX
            # Note: NetworkX doesn't have built-in k-shortest paths for weighted graphs
            # We'll use a workaround: find shortest path, then find alternatives by removing edges
            alternative_paths = []
            
            # First path (shortest)
            try:
                if max_stops is not None and max_stops <= 2:
                    first_path = self._fast_constrained_path(
                        working_graph, source_id, dest_id, max_stops=max_stops
                    )
                    if first_path is None:
                        return {"error": f"No path found within {max_stops} stops"}
                    first_distance = self._calculate_path_weight(working_graph, first_path)
                elif max_stops is not None:
                    first_path = self._find_path_with_stop_limit(
                        working_graph, source_id, dest_id, max_stops=max_stops
                    )
                    if first_path is None:
                        return {"error": f"No path found within {max_stops} stops"}
                    first_distance = self._calculate_path_weight(working_graph, first_path)
                else:
                    first_path = nx.shortest_path(working_graph, source_id, dest_id, weight='weight')
                    first_distance = nx.shortest_path_length(working_graph, source_id, dest_id, weight='weight')
                
                alternative_paths.append({
                    "path": [self._get_iata_by_airport_id(node) for node in first_path],
                    "distance_km": first_distance,
                    "stops": len(first_path) - 2,
                    "transfer_hubs": [self._get_iata_by_airport_id(node) for node in first_path[1:-1]],
                    "rank": 1
                })
            except nx.NetworkXNoPath:
                return {"error": "No path found"}
            
            # Find alternative paths by trying different approaches
            # Method 1: Remove edges from shortest path and find new paths
            temp_graph = working_graph.copy()
            for i in range(len(first_path) - 1):
                if temp_graph.has_edge(first_path[i], first_path[i+1]):
                    temp_graph.remove_edge(first_path[i], first_path[i+1])
                    
                    try:
                        alt_path = nx.shortest_path(temp_graph, source_id, dest_id, weight='weight')
                        alt_distance = nx.shortest_path_length(temp_graph, source_id, dest_id, weight='weight')
                        
                        # Check if this is a different path
                        if alt_path != first_path and alt_path not in [p["path"] for p in alternative_paths]:
                            alternative_paths.append({
                                "path": [self._get_iata_by_airport_id(node) for node in alt_path],
                                "distance_km": alt_distance,
                                "stops": len(alt_path) - 2,
                                "transfer_hubs": [self._get_iata_by_airport_id(node) for node in alt_path[1:-1]],
                                "rank": len(alternative_paths) + 1
                            })
                            
                            if len(alternative_paths) >= k:
                                break
                    except nx.NetworkXNoPath:
                        continue
                    
                    # Restore edge for next iteration
                    temp_graph.add_edge(first_path[i], first_path[i+1], **working_graph[first_path[i]][first_path[i+1]])
            
            # Method 2: Find paths through different major hubs
            if len(alternative_paths) < k:
                top_hubs_result = self.analyze_hubs(top_n=10)
                major_hubs = [self._get_airport_id_by_iata(hub['airport']) for hub in top_hubs_result['top_hubs'] 
                             if hub['airport'] not in [source_iata, dest_iata]]
                
                for hub_id in major_hubs[:5]:  # Try top 5 hubs to reduce runtime
                    if hub_id in working_graph.nodes() and hub_id not in first_path:
                        try:
                            # Path through this hub
                            path1 = nx.shortest_path(working_graph, source_id, hub_id, weight='weight')
                            path2 = nx.shortest_path(working_graph, hub_id, dest_id, weight='weight')
                            
                            # Combine paths (remove duplicate hub)
                            combined_path = path1 + path2[1:]
                            combined_distance = nx.shortest_path_length(working_graph, source_id, hub_id, weight='weight') + \
                                               nx.shortest_path_length(working_graph, hub_id, dest_id, weight='weight')
                            
                            # Check if different from existing paths
                            path_iata = [self._get_iata_by_airport_id(node) for node in combined_path]
                            if path_iata not in [p["path"] for p in alternative_paths]:
                                alternative_paths.append({
                                    "path": path_iata,
                                    "distance_km": combined_distance,
                                    "stops": len(combined_path) - 2,
                                    "transfer_hubs": [self._get_iata_by_airport_id(node) for node in combined_path[1:-1]],
                                    "rank": len(alternative_paths) + 1,
                                    "via_hub": self._get_iata_by_airport_id(hub_id)
                                })
                                
                                if len(alternative_paths) >= k:
                                    break
                        except nx.NetworkXNoPath:
                            continue
            
            # Calculate flight time for each path
            for path_info in alternative_paths:
                # Build legs from path (convert IATA back to airport_ids)
                path_iata_list = path_info['path']
                path_nodes = []
                for iata in path_iata_list:
                    airport_id = self._get_airport_id_by_iata(iata)
                    if airport_id:
                        path_nodes.append(airport_id)
                
                legs = []
                for i in range(len(path_nodes) - 1):
                    if self.graph.has_edge(path_nodes[i], path_nodes[i+1]):
                        edge_data = self.graph[path_nodes[i]][path_nodes[i+1]]
                        distance = edge_data.get('distance_km', 0)
                        if distance and distance > 0:
                            legs.append({
                                "distance_km": distance
                            })
                
                # Calculate time for this path
                if legs:
                    time_info = compute_total_route_time(legs, use_random_transit=True)
                    if time_info:
                        path_info.update({
                            "total_flight_time_hours": time_info.get('total_flight_time_hours'),
                            "total_transit_time_hours": time_info.get('total_transit_time_hours'),
                            "total_route_time_hours": time_info.get('total_route_time_hours'),
                            "leg_times": time_info.get('leg_times', []),
                            "transit_times": time_info.get('transit_times', [])
                        })
            
            # Sort by distance
            alternative_paths.sort(key=lambda x: x['distance_km'])
            
            return {
                "source": source_iata,
                "destination": dest_iata,
                "total_paths_found": len(alternative_paths),
                "paths": alternative_paths[:k],
                "best_path": alternative_paths[0] if alternative_paths else None
            }
            
        except Exception as e:
            return {"error": f"Error finding robust paths: {str(e)}"}
    
    def suggest_alternative_transfer_hubs(
        self,
        source_iata: str,
        dest_iata: str,
        top_n: int = 5
    ) -> Dict[str, Any]:
        """
        Suggest alternative transfer hubs for a route
        This addresses the goal: "highlight alternative hubs"
        
        Args:
            source_iata: Source airport code
            dest_iata: Destination airport code
            top_n: Number of alternative hubs to suggest
            
        Returns:
            Dictionary with alternative transfer hub suggestions
        """
        source_id = self._get_airport_id_by_iata(source_iata)
        dest_id = self._get_airport_id_by_iata(dest_iata)
        
        if not source_id or not dest_id:
            return {"error": "Airport not found"}
        
        # Get hub analysis
        hubs_result = self.analyze_hubs(top_n=50)
        all_hubs = hubs_result['top_hubs']
        
        # Find hubs that can serve as transfer points
        alternative_hubs = []
        
        for hub in all_hubs:
            hub_iata = hub['airport']
            hub_id = self._get_airport_id_by_iata(hub_iata)
            
            if hub_id and hub_id not in [source_id, dest_id]:
                # Check if this hub can serve as transfer
                try:
                    # Check if path exists: source -> hub -> dest
                    path1_exists = nx.has_path(self.graph, source_id, hub_id)
                    path2_exists = nx.has_path(self.graph, hub_id, dest_id)
                    
                    if path1_exists and path2_exists:
                        # Calculate total distance through this hub
                        dist1 = nx.shortest_path_length(self.graph, source_id, hub_id, weight='weight')
                        dist2 = nx.shortest_path_length(self.graph, hub_id, dest_id, weight='weight')
                        total_dist = dist1 + dist2
                        
                        # Get direct path distance for comparison
                        try:
                            direct_dist = nx.shortest_path_length(self.graph, source_id, dest_id, weight='weight')
                            efficiency = (direct_dist / total_dist) * 100 if total_dist > 0 else 0
                        except nx.NetworkXNoPath:
                            direct_dist = float('inf')
                            efficiency = 100  # This hub provides connectivity
                        
                        # Calculate flight time for route through this hub
                        legs = []
                        # Leg 1: source -> hub
                        try:
                            path1_nodes = nx.shortest_path(self.graph, source_id, hub_id, weight='weight')
                            for i in range(len(path1_nodes) - 1):
                                if self.graph.has_edge(path1_nodes[i], path1_nodes[i+1]):
                                    edge_data = self.graph[path1_nodes[i]][path1_nodes[i+1]]
                                    distance = edge_data.get('distance_km', 0)
                                    if distance and distance > 0:
                                        legs.append({"distance_km": distance})
                        except nx.NetworkXNoPath:
                            pass
                        
                        # Leg 2: hub -> dest
                        try:
                            path2_nodes = nx.shortest_path(self.graph, hub_id, dest_id, weight='weight')
                            for i in range(len(path2_nodes) - 1):
                                if self.graph.has_edge(path2_nodes[i], path2_nodes[i+1]):
                                    edge_data = self.graph[path2_nodes[i]][path2_nodes[i+1]]
                                    distance = edge_data.get('distance_km', 0)
                                    if distance and distance > 0:
                                        legs.append({"distance_km": distance})
                        except nx.NetworkXNoPath:
                            pass
                        
                        hub_info = {
                            "hub": hub_iata,
                            "name": hub['name'],
                            "city": hub['city'],
                            "country": hub['country'],
                            "degree_centrality": hub['degree_centrality'],
                            "betweenness_centrality": hub['betweenness_centrality'],
                            "total_distance_km": total_dist,
                            "direct_distance_km": direct_dist,
                            "efficiency_percent": efficiency,
                            "path": f"{source_iata} -> {hub_iata} -> {dest_iata}"
                        }
                        
                        # Add flight time if legs available
                        if legs:
                            time_info = compute_total_route_time(legs, use_random_transit=True)
                            if time_info:
                                hub_info.update({
                                    "total_flight_time_hours": time_info.get('total_flight_time_hours'),
                                    "total_transit_time_hours": time_info.get('total_transit_time_hours'),
                                    "total_route_time_hours": time_info.get('total_route_time_hours')
                                })
                        
                        alternative_hubs.append(hub_info)
                except Exception:
                    continue
        
        # Sort by efficiency and centrality
        alternative_hubs.sort(key=lambda x: (x['efficiency_percent'], x['degree_centrality']), reverse=True)
        
        return {
            "source": source_iata,
            "destination": dest_iata,
            "alternative_hubs": alternative_hubs[:top_n],
            "total_hubs_analyzed": len(alternative_hubs)
        }
    
    def get_airport_coordinates(self, iata_codes: List[str]) -> List[Tuple[float, float, str]]:
        """
        Get coordinates for airports by IATA codes
        
        Args:
            iata_codes: List of IATA codes
            
        Returns:
            List of (lat, lon, iata) tuples
        """
        coordinates = []
        for iata in iata_codes:
            airport_id = self._get_airport_id_by_iata(iata)
            if airport_id and airport_id in self.graph.nodes():
                node_data = self.graph.nodes[airport_id]
                coordinates.append((
                    node_data.get('latitude', 0),
                    node_data.get('longitude', 0),
                    iata
                ))
        return coordinates
    
    def _get_airport_id_by_iata(self, iata: str) -> Optional[int]:
        """Get airport ID by IATA code"""
        airport = self.airports_df[self.airports_df['iata'] == iata]
        return airport['airport_id'].iloc[0] if not airport.empty else None
    
    def _get_iata_by_airport_id(self, airport_id: int) -> str:
        """Get IATA code by airport ID"""
        airport = self.airports_df[self.airports_df['airport_id'] == airport_id]
        return airport['iata'].iloc[0] if not airport.empty else str(airport_id)
    
    def _get_airport_info(self, airport_id: int) -> Optional[Dict[str, Any]]:
        """Get airport information by ID"""
        airport = self.airports_df[self.airports_df['airport_id'] == airport_id]
        if not airport.empty:
            return {
                'iata': airport.iloc[0]['iata'],
                'name': airport.iloc[0]['name'],
                'city': airport.iloc[0]['city'],
                'country': airport.iloc[0]['country'],
                'latitude': airport.iloc[0]['latitude'],
                'longitude': airport.iloc[0]['longitude']
            }
        return None


def load_flight_data(data_dir: str = "data/cleaned") -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load cleaned flight data for Streamlit app
    
    Args:
        data_dir: Directory containing cleaned CSV files
        
    Returns:
        Tuple of (airports_df, routes_df)
    """
    import os
    from pathlib import Path
    
    data_path = Path(data_dir)
    
    # Load airports
    airports_file = data_path / "airports_cleaned.csv"
    if airports_file.exists():
        airports_df = pd.read_csv(airports_file)
    else:
        raise FileNotFoundError(f"Airports file not found: {airports_file}")
    
    # Load routes
    routes_file = data_path / "routes_graph.csv"
    if routes_file.exists():
        routes_df = pd.read_csv(routes_file)
    else:
        raise FileNotFoundError(f"Routes file not found: {routes_file}")
    
    return airports_df, routes_df


def create_flight_analyzer(data_dir: str = "data/cleaned") -> FlightGraphAnalyzer:
    """
    Create FlightGraphAnalyzer instance with loaded data
    
    Args:
        data_dir: Directory containing cleaned CSV files
        
    Returns:
        FlightGraphAnalyzer instance
    """
    airports_df, routes_df = load_flight_data(data_dir)
    return FlightGraphAnalyzer(airports_df, routes_df)
