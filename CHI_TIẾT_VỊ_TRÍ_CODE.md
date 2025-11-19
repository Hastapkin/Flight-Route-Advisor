# CHI TIẾT VỊ TRÍ CODE - Flight Route Advisor

## 1. Dataset: OpenFlights

### Vị trí: `pipeline/loader.py`

**Code load dữ liệu từ OpenFlights:**

```python
# Dòng 11-13: URLs của OpenFlights
AIRPORTS_URL = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat"
AIRLINES_URL = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airlines.dat"
ROUTES_URL = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/routes.dat"

# Dòng 30-84: Class OpenFlightsLoader
class OpenFlightsLoader:
    def load(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        # Load từ URL hoặc local file
        airports_df = _read_openflights_csv(_fetch_csv(AIRPORTS_URL), airport_columns)
        airlines_df = _read_openflights_csv(_fetch_csv(AIRLINES_URL), airline_columns)
        routes_df = _read_openflights_csv(_fetch_csv(ROUTES_URL), route_columns)
```

**File liên quan:**
- `config.py` (dòng 16-19): Cũng có cấu hình URL OpenFlights

---

## 2. Robust Transfer Paths

### Vị trí chính: `pipeline/graph_analyzer.py`

**Function tìm đường chuyển bay tối ưu:**

```python
# Dòng 63-125: find_shortest_path()
def find_shortest_path(self, source_iata: str, dest_iata: str) -> Dict[str, Any]:
    """
    Find shortest path between two airports using Dijkstra algorithm
    """
    # Tìm shortest path với Dijkstra
    path_nodes = nx.shortest_path(
        self.graph, 
        source_id, 
        dest_id, 
        weight='weight'  # Sử dụng distance làm weight
    )
    
    # Tính tổng khoảng cách
    total_distance = nx.shortest_path_length(
        self.graph, 
        source_id, 
        dest_id, 
        weight='weight'
    )
    
    # Trả về path với stops, legs, distance
    return {
        "source": source_iata,
        "destination": dest_iata,
        "path": path_iata,  # Danh sách các sân bay trung gian
        "total_distance_km": total_distance,
        "legs": legs,  # Chi tiết từng chặng bay
        "stops": len(path_nodes) - 2  # Số điểm dừng
    }
```

### Vị trí UI: `app/streamlit_app.py`

**Hiển thị trong Streamlit app:**

```python
# Dòng 413-432: Mode "Shortest Route"
if mode == "Shortest Route":
    source_airport = st.sidebar.selectbox("From Airport", airport_options)
    dest_airport = st.sidebar.selectbox("To Airport", airport_options)
    
    if st.sidebar.button("Find Route", type="primary"):
        result = analyzer.find_shortest_path(source_airport, dest_airport)
        display_shortest_path_result(result, analyzer)

# Dòng 128-199: display_shortest_path_result()
# Hiển thị route với map visualization (Folium)
```

**Kết quả trả về:**
- Path: Danh sách các sân bay (ví dụ: SGN -> DXB -> LHR)
- Total distance: Tổng khoảng cách
- Stops: Số điểm dừng
- Legs: Chi tiết từng chặng bay
- Map visualization: Bản đồ tương tác với Folium

---

## 3. Alternative Hubs

### Vị trí chính: `pipeline/graph_analyzer.py`

**Function phân tích hubs và backup hubs:**

```python
# Dòng 127-179: analyze_hubs()
def analyze_hubs(self, country: str = None, top_n: int = 10) -> Dict[str, Any]:
    """
    Analyze airport hubs using centrality measures
    """
    # Tính 4 loại centrality
    degree_centrality = nx.degree_centrality(self.graph)
    betweenness_centrality = nx.betweenness_centrality(self.graph, weight='weight')
    closeness_centrality = nx.closeness_centrality(self.graph, distance='weight')
    pagerank = nx.pagerank(self.graph, weight='weight')
    
    # Sắp xếp theo degree centrality
    hubs_data.sort(key=lambda x: x['degree_centrality'], reverse=True)
    
    # Top hubs và backup hubs
    top_hubs = hubs_data[:top_n]
    backup_hubs = hubs_data[top_n:top_n*2]  # BACKUP HUBS (alternative hubs)
    
    return {
        "country": country or "Global",
        "top_hubs": top_hubs,
        "backup_hubs": backup_hubs,  # Đây là alternative hubs
        "total_airports": len(hubs_data)
    }
```

### Vị trí UI: `app/streamlit_app.py`

**Hiển thị trong Streamlit app:**

```python
# Dòng 434-454: Mode "Hub Analysis"
elif mode == "Hub Analysis":
    selected_country = st.sidebar.selectbox("Select Country", countries)
    top_n = st.sidebar.slider("Number of Top Hubs", 5, 20, 10)
    
    if st.sidebar.button("Analyze Hubs", type="primary"):
        result = analyzer.analyze_hubs(country_filter, top_n)
        display_hub_analysis_result(result)

# Dòng 233-249: Hiển thị backup hubs
if result['backup_hubs']:
    st.markdown("### Backup Hubs")  # Alternative hubs được hiển thị ở đây
    backup_df = pd.DataFrame(backup_data)
    st.dataframe(backup_df, use_container_width=True)
```

**Kết quả trả về:**
- Top hubs: Top N hubs theo centrality
- **Backup hubs**: Alternative hubs (top N+1 đến top 2N) - đây chính là alternative hubs
- Centrality measures: Degree, Betweenness, Closeness, PageRank

---

## 4. Shortest Paths Method

### Vị trí: `pipeline/graph_analyzer.py`

**Sử dụng NetworkX shortest_path với Dijkstra:**

```python
# Dòng 84-99: Tìm shortest path
try:
    # Find shortest path using Dijkstra algorithm
    path_nodes = nx.shortest_path(
        self.graph,      # NetworkX directed graph
        source_id,       # Source airport ID
        dest_id,         # Destination airport ID
        weight='weight'  # Weight = distance_km
    )
    
    # Calculate total distance
    total_distance = nx.shortest_path_length(
        self.graph, 
        source_id, 
        dest_id, 
        weight='weight'
    )
```

**Graph được build từ routes:**

```python
# Dòng 28-61: _build_graph()
def _build_graph(self) -> None:
    """Build NetworkX graph from routes and airports data"""
    self.graph = nx.DiGraph()  # Directed graph
    
    # Add airport nodes
    for _, airport in self.airports_df.iterrows():
        self.graph.add_node(airport['airport_id'], ...)
    
    # Add route edges với weight = distance_km
    for _, route in self.routes_df.iterrows():
        if pd.notna(route.get('distance_km')):
            self.graph.add_edge(
                route['source_airport_id'],
                route['destination_airport_id'],
                weight=float(route['distance_km']),  # Weight cho shortest path
                distance_km=float(route['distance_km'])
            )
```

**Algorithm:** Dijkstra (mặc định của NetworkX shortest_path với weighted graph)

---

## 5. Hub Removal What-If Method

### Vị trí chính: `pipeline/graph_analyzer.py`

**Function phân tích what-if khi loại bỏ hub:**

```python
# Dòng 196-271: hub_removal_analysis()
def hub_removal_analysis(self, hub_iata: str) -> Dict[str, Any]:
    """
    Analyze network impact when removing a specific hub (what-if analysis)
    """
    # 1. Lấy network stats ban đầu
    original_stats = self.get_network_stats()
    
    # 2. Tạo copy graph và remove hub
    graph_without_hub = self.graph.copy()
    graph_without_hub.remove_node(hub_id)  # Remove hub
    
    # 3. Lấy network stats sau khi remove
    remaining_stats = {
        "total_nodes": graph_without_hub.number_of_nodes(),
        "total_edges": graph_without_hub.number_of_edges(),
        "density": nx.density(graph_without_hub),
        "is_strongly_connected": nx.is_strongly_connected(graph_without_hub),
        ...
    }
    
    # 4. Tính impact metrics
    impact_metrics = {
        "nodes_lost": original_stats['total_nodes'] - remaining_stats['total_nodes'],
        "edges_lost": original_stats['total_edges'] - remaining_stats['total_edges'],
        "density_change": remaining_stats['density'] - original_stats['density'],
        "connectivity_broken": ...,
        "components_increase": ...
    }
    
    # 5. Tìm affected routes
    affected_routes = [...]  # Routes đi qua hub này
    
    # 6. Tìm alternative paths
    alternative_paths = self._find_alternative_paths(hub_id, graph_without_hub)
    
    # 7. Đánh giá severity
    severity = self._assess_removal_severity(impact_metrics)
    
    return {
        "hub_removed": hub_iata,
        "original_stats": original_stats,
        "remaining_stats": remaining_stats,
        "impact_metrics": impact_metrics,
        "affected_routes": affected_routes,
        "alternative_paths": alternative_paths,  # Alternative paths sau khi remove hub
        "severity": severity  # CRITICAL, HIGH, MEDIUM, LOW
    }
```

**Function tìm alternative paths:**

```python
# Dòng 273-310: _find_alternative_paths()
def _find_alternative_paths(self, removed_hub_id: int, graph_without_hub: nx.DiGraph):
    """Find alternative paths for routes that were affected by hub removal"""
    # Tìm các routes bị ảnh hưởng
    # Tìm alternative path trong graph_without_hub
    alt_path = nx.shortest_path(graph_without_hub, source_id, dest_id, weight='weight')
```

### Vị trí UI: `app/streamlit_app.py`

**Hiển thị trong Streamlit app:**

```python
# Dòng 456-474: Mode "Hub Removal What-If"
elif mode == "Hub Removal What-If":
    selected_hub = st.sidebar.selectbox("Select Hub to Remove", hub_options)
    
    if st.sidebar.button("Analyze Impact", type="primary"):
        result = analyzer.hub_removal_analysis(selected_hub)
        display_hub_removal_result(result)

# Dòng 252-354: display_hub_removal_result()
# Hiển thị:
# - Impact metrics (nodes lost, edges lost, density change)
# - Network comparison (before/after)
# - Affected routes
# - Alternative paths
```

**Kết quả phân tích:**
- Impact metrics: Nodes lost, edges lost, density change, connectivity
- Network comparison: Before vs After removal
- Affected routes: Routes đi qua hub bị remove
- **Alternative paths**: Đường thay thế sau khi remove hub
- Severity: CRITICAL, HIGH, MEDIUM, LOW

---

## 6. Centrality Method

### Vị trí: `pipeline/graph_analyzer.py`

**Tính 4 loại centrality measures:**

```python
# Dòng 141-145: Trong analyze_hubs()
# Calculate centrality measures
degree_centrality = nx.degree_centrality(self.graph)
betweenness_centrality = nx.betweenness_centrality(self.graph, weight='weight')
closeness_centrality = nx.closeness_centrality(self.graph, distance='weight')
pagerank = nx.pagerank(self.graph, weight='weight')
```

**Sử dụng trong hub analysis:**

```python
# Dòng 152-161: Gán centrality vào hub info
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
```

**Cũng được tính trong notebook cho Gephi:**

```python
# notebook/flight_route.ipynb (dòng 1715-1718)
degree_centrality = nx.degree_centrality(G_gephi)
betweenness_centrality = nx.betweenness_centrality(G_gephi, weight='weight')
closeness_centrality = nx.closeness_centrality(G_gephi, distance='weight')
pagerank = nx.pagerank(G_gephi, weight='weight')

# Thêm vào nodes cho Gephi visualization
for node in G_gephi.nodes():
    G_gephi.nodes[node]['degree_centrality'] = degree_centrality.get(node, 0)
    G_gephi.nodes[node]['betweenness_centrality'] = betweenness_centrality.get(node, 0)
    G_gephi.nodes[node]['closeness_centrality'] = closeness_centrality.get(node, 0)
    G_gephi.nodes[node]['pagerank'] = pagerank.get(node, 0)
```

**4 loại centrality:**
1. **Degree Centrality**: Số lượng connections
2. **Betweenness Centrality**: Tần suất nằm trên shortest paths
3. **Closeness Centrality**: Khoảng cách trung bình đến các nodes khác
4. **PageRank**: Tầm quan trọng dựa trên connections

---

## 7. Notebook Deliverable

### Vị trí: `notebook/flight_route.ipynb`

**Nội dung notebook bao gồm:**

1. **Data Loading & Cleaning:**
   - Load OpenFlights data
   - Clean airports, airlines, routes
   - Calculate distances

2. **Graph Building:**
   - Tạo NetworkX graph từ routes
   - Add nodes (airports) và edges (routes)

3. **Network Analysis:**
   - Tính centrality measures (dòng 1715-1718)
   - Network statistics
   - Hub analysis

4. **Gephi Export:**
   - Export multiple network views (dòng 1788-1930)
   - 5 file .gexf cho Gephi visualization

**File:** `notebook/flight_route.ipynb` (2021 dòng)

---

## 8. Gephi Visualization Deliverable

### Vị trí: `notebook/flight_route.ipynb`

**Code export Gephi files:**

```python
# Dòng 1788-1930: Export multiple network views
# 1. FULL NETWORK
G_full = create_clean_graph(G_gephi)
nx.write_gexf(G_full, '../data/gephi/flight_network_full.gexf')

# 2. MAJOR HUBS NETWORK (top 20% by degree centrality)
top_20_percent = int(len(degree_centrality) * 0.2)
top_hubs_nodes = [node for node, _ in sorted(degree_centrality.items(), ...)[:top_20_percent]]
G_major_hubs = G_gephi.subgraph(top_hubs_nodes)
nx.write_gexf(G_major_hubs_clean, '../data/gephi/flight_network_major_hubs.gexf')

# 3. LONG DISTANCE NETWORK (routes > 5000km)
long_distance_edges = [(u, v) for u, v, d in G_gephi.edges(data=True) if d.get('distance_km', 0) > 5000]
G_long_distance = G_gephi.edge_subgraph(long_distance_edges)
nx.write_gexf(G_long_distance_clean, '../data/gephi/flight_network_long_distance.gexf')

# 4. INTERNATIONAL NETWORK (cross-border routes)
international_edges = [...]
G_international = G_gephi.edge_subgraph(international_edges)
nx.write_gexf(G_international_clean, '../data/gephi/flight_network_international.gexf')

# 5. COUNTRY LEVEL NETWORK (country aggregation)
G_country = create_country_level_graph(...)
nx.write_gexf(G_country_clean, '../data/gephi/flight_network_country_level.gexf')
```

**Files được tạo:**

1. `data/gephi/flight_network_full.gexf` - Complete network (7698 nodes, 36588 edges)
2. `data/gephi/flight_network_major_hubs.gexf` - Top 20% hubs (1539 nodes, 31899 edges)
3. `data/gephi/flight_network_long_distance.gexf` - Routes > 5000km (308 nodes, 2550 edges)
4. `data/gephi/flight_network_international.gexf` - Cross-border routes (1169 nodes, 19461 edges)
5. `data/gephi/flight_network_country_level.gexf` - Country aggregation (237 countries, 4553 connections)

**Cấu hình trong config:**

```python
# config.py (dòng 44-68)
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
    ...
}
```

---

## TỔNG KẾT VỊ TRÍ CODE

| Yêu cầu | File chính | Dòng code | Function/Method |
|---------|-----------|-----------|-----------------|
| **Dataset: OpenFlights** | `pipeline/loader.py` | 11-84 | `OpenFlightsLoader.load()` |
| **Robust Transfer Paths** | `pipeline/graph_analyzer.py` | 63-125 | `find_shortest_path()` |
| **Alternative Hubs** | `pipeline/graph_analyzer.py` | 127-179 | `analyze_hubs()` -> `backup_hubs` |
| **Shortest Paths Method** | `pipeline/graph_analyzer.py` | 84-99 | `nx.shortest_path()` |
| **Hub Removal What-If** | `pipeline/graph_analyzer.py` | 196-271 | `hub_removal_analysis()` |
| **Centrality Method** | `pipeline/graph_analyzer.py` | 141-145 | 4 centrality measures |
| **Notebook** | `notebook/flight_route.ipynb` | Toàn bộ | Jupyter notebook |
| **Gephi Visualization** | `notebook/flight_route.ipynb` | 1788-1930 | `nx.write_gexf()` |

**UI Integration:**
- `app/streamlit_app.py`: Tất cả features đều có UI trong Streamlit app
