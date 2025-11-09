# KIỂM TRA YÊU CẦU ĐỀ TÀI - Flight Route Advisor

## Yêu cầu đề tài: A3. Flight Route Advisor

**Dataset**: OpenFlights routes (airports graph)  
**Goal**: Suggest robust transfer paths; highlight alternative hubs  
**Methods**: Shortest paths + hub removal what-if + centrality  
**Deliverables**: notebook + map-style viz (Gephi) + report  
**Ref**: openflights.org

---

## KIỂM TRA CHI TIẾT

### 1. Dataset: OpenFlights routes (airports graph)

**Bằng chứng**:
- File `pipeline/loader.py` load dữ liệu từ OpenFlights:
  - `AIRPORTS_URL = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat"`
  - `AIRLINES_URL = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airlines.dat"`
  - `ROUTES_URL = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/routes.dat"`
- File `config.py` cũng có cấu hình URL OpenFlights
- Dữ liệu được xử lý và lưu trong `data/cleaned/`:
  - `airports_cleaned.csv`
  - `airlines_cleaned.csv`
  - `routes_cleaned.csv`
  - `routes_graph.csv` (có thêm distance_km)

---

### 2. Goal: Suggest robust transfer paths

**Bằng chứng**:
- **Shortest Path Analysis** trong `app/streamlit_app.py`:
  - Function `find_shortest_path()` trong `pipeline/graph_analyzer.py` (dòng 63-125)
  - Sử dụng Dijkstra algorithm (`nx.shortest_path()`)
  - Hiển thị route với stops, distance, và map visualization
  - Tìm đường chuyển bay tối ưu giữa 2 sân bay bất kỳ

**Vị trí code**:
- `pipeline/graph_analyzer.py`: `find_shortest_path()` method
- `app/streamlit_app.py`: Mode "Shortest Route" (dòng 413-432)

---

### 3. Goal: Highlight alternative hubs 

**Bằng chứng**:
- **Hub Analysis** trong `app/streamlit_app.py`:
  - Function `analyze_hubs()` trong `pipeline/graph_analyzer.py` (dòng 127-179)
  - Tính toán centrality measures (degree, betweenness, closeness, PageRank)
  - Hiển thị top hubs và backup hubs
  - Có thể filter theo country hoặc global

**Vị trí code**:
- `pipeline/graph_analyzer.py`: `analyze_hubs()` method (dòng 127-179)
- `app/streamlit_app.py`: Mode "Hub Analysis" (dòng 434-454)
- Hiển thị backup hubs trong `display_hub_analysis_result()` (dòng 233-249)

---

### 4. Methods: Shortest paths

**Bằng chứng**:
- Sử dụng NetworkX `nx.shortest_path()` với Dijkstra algorithm
- Weighted graph sử dụng distance_km làm weight
- Code trong `pipeline/graph_analyzer.py`:
  ```python
  path_nodes = nx.shortest_path(
      self.graph, 
      source_id, 
      dest_id, 
      weight='weight'
  )
  ```

**Vị trí code**:
- `pipeline/graph_analyzer.py`: `find_shortest_path()` (dòng 63-125)

---

### 5. Methods: Hub removal what-if

**Bằng chứng**:
- Function `hub_removal_analysis()` trong `pipeline/graph_analyzer.py` (dòng 196-271)
- Phân tích impact khi loại bỏ một hub:
  - So sánh network stats trước/sau
  - Tính impact metrics (nodes lost, edges lost, density change, connectivity)
  - Tìm alternative paths cho các routes bị ảnh hưởng
  - Đánh giá severity (CRITICAL, HIGH, MEDIUM, LOW)
- Function `_find_alternative_paths()` tìm đường thay thế (dòng 273-310)

**Vị trí code**:
- `pipeline/graph_analyzer.py`: `hub_removal_analysis()` (dòng 196-271)
- `app/streamlit_app.py`: Mode "Hub Removal What-If" (dòng 456-474)
- Hiển thị kết quả trong `display_hub_removal_result()` (dòng 252-354)

---

### 6. Methods: Centrality

**Bằng chứng**:
- Tính toán 4 loại centrality measures:
  1. **Degree Centrality**: `nx.degree_centrality()`
  2. **Betweenness Centrality**: `nx.betweenness_centrality()` (weighted)
  3. **Closeness Centrality**: `nx.closeness_centrality()` (weighted)
  4. **PageRank**: `nx.pagerank()` (weighted)

**Vị trí code**:
- `pipeline/graph_analyzer.py`: `analyze_hubs()` (dòng 141-145)
- `notebook/flight_route.ipynb`: Tính centrality cho Gephi visualization (dòng 1715-1718)

---

### 7. Deliverables: Notebook

**Bằng chứng**:
- File `notebook/flight_route.ipynb` tồn tại
- Notebook chứa:
  - Data loading và cleaning
  - Graph building với NetworkX
  - Centrality calculations
  - Gephi export functions
  - Network analysis và visualization

**Vị trí**: `notebook/flight_route.ipynb`

---

### 8. Deliverables: Map-style viz (Gephi)

**Bằng chứng**:
- Có 5 file Gephi (.gexf) trong `data/gephi/`:
  1. `flight_network_full.gexf` - Complete network
  2. `flight_network_major_hubs.gexf` - Top 20% hubs
  3. `flight_network_long_distance.gexf` - Routes > 5000km
  4. `flight_network_international.gexf` - Cross-border routes
  5. `flight_network_country_level.gexf` - Country aggregation

- Code export trong `notebook/flight_route.ipynb`:
  - Sử dụng `nx.write_gexf()` để export
  - Có function `create_clean_graph()` để clean attributes cho Gephi
  - Export multiple network views (dòng 1788-1856)

**Vị trí**:
- Files: `data/gephi/*.gexf` (5 files)
- Code: `notebook/flight_route.ipynb` (dòng 1788-1856)

