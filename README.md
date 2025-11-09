# ✈️ Flight Route Advisor

A comprehensive flight network analysis system with interactive visualization and route optimization capabilities.

## 🎯 Project Overview

This project analyzes global flight networks using OpenFlights data, providing:
- **Route Optimization**: Find shortest paths between airports
- **Hub Analysis**: Identify critical airports and their importance
- **What-If Analysis**: Assess network impact when removing hubs
- **Interactive Visualization**: Gephi network graphs and Streamlit web app

## 🚀 Quick Start

### 1. Installation
```bash
# Clone repository
git clone <repository-url>
cd Flight-Route-Advisor

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Application
```bash
# Run everything (pipeline + app)
python run_app.py

# Or run separately:
# 1. Process data
python -m pipeline.main_pipeline

# 2. Start web app
streamlit run app/streamlit_app.py
```

## 📊 Features

### 1. **Shortest Route Analysis**
- Find optimal flight paths between any two airports
- Display distance, stops, and transfer airports
- Interactive map visualization with Folium

### 2. **Hub Analysis**
- Identify top airports by centrality measures
- Analyze hubs by country or globally
- Degree, Betweenness, Closeness, and PageRank centrality

### 3. **Hub Removal What-If Analysis** ⭐
- Simulate removing critical hubs
- Assess network impact and resilience
- Find alternative routes and backup hubs

### 4. **Network Visualization**
- Export to Gephi for advanced network analysis
- Multiple network views (full, major hubs, long-distance, international)
- Interactive network exploration

## 🗂️ Project Structure

```
Flight-Route-Advisor/
├── 📁 app/
│   └── streamlit_app.py          # Interactive web application
├── 📁 pipeline/
│   ├── loader.py                 # Data loading
│   ├── cleaner_*.py              # Data cleaning modules
│   ├── utils_distance.py         # Distance calculations
│   ├── graph_analyzer.py         # Network analysis
│   └── main_pipeline.py          # Main processing pipeline
├── 📁 notebook/
│   └── flight_route.ipynb        # Gephi export & analysis
├── 📁 data/
│   ├── cleaned/                  # Processed CSV files
│   └── gephi/                    # Gephi visualization files
├── 📄 requirements.txt           # Python dependencies
├── 📄 run_app.py                # Application launcher
├── 📄 test_app.py               # Testing & validation
└── 📄 report_template.md        # Analysis report template
```

## 🔧 Technical Details

### Data Pipeline
1. **Loading**: OpenFlights raw data (.dat files)
2. **Cleaning**: Remove invalid entries, standardize formats
3. **Enrichment**: Calculate distances using Haversine formula
4. **Graph Building**: Create NetworkX directed graph
5. **Analysis**: Centrality measures and path finding

### Technologies Used
- **Python**: Core language
- **Pandas**: Data manipulation
- **NetworkX**: Graph analysis and algorithms
- **Streamlit**: Web application framework
- **Folium**: Interactive maps
- **Gephi**: Network visualization

## 📈 Analysis Capabilities

### Network Metrics
- **Connectivity**: Strong/weak connectivity analysis
- **Centrality**: Multiple centrality measures
- **Resilience**: Hub removal impact assessment
- **Efficiency**: Route optimization algorithms

### Visualization Options
- **Interactive Maps**: Real-time route visualization
- **Network Graphs**: Gephi-based network analysis
- **Statistical Charts**: Centrality and connectivity metrics
- **Comparative Analysis**: Before/after hub removal

## 🎨 Gephi Visualization Guide

### Network Files Available
- `flight_network_full.gexf` - Complete network
- `flight_network_major_hubs.gexf` - Top 20% hubs
- `flight_network_long_distance.gexf` - Routes > 5000km
- `flight_network_international.gexf` - Cross-border routes
- `flight_network_country_level.gexf` - Country aggregation

### Gephi Setup (Free Version)
1. **Layout**: ForceAtlas 2 (Scaling: 1000-2000, Gravity: 0.1-0.3)
2. **Node Size**: PageRank centrality
3. **Node Color**: Modularity Class or Country
4. **Edge**: Weight by distance
5. **Filters**: Degree Range (min 3-5) for clarity

## 🔍 Usage Examples

### Find Shortest Route
```python
# In Streamlit app
Source: SGN (Ho Chi Minh City)
Destination: LHR (London Heathrow)
Result: SGN → DXB → LHR (2 stops, 10,432 km)
```

### Hub Analysis
```python
# Top 5 Global Hubs
1. ATL - Hartsfield-Jackson Atlanta (Degree: 0.0234)
2. ORD - Chicago O'Hare (Degree: 0.0218)
3. DFW - Dallas/Fort Worth (Degree: 0.0201)
4. DEN - Denver International (Degree: 0.0195)
5. LAX - Los Angeles International (Degree: 0.0189)
```

### What-If Analysis
```python
# Remove ATL (Atlanta) - CRITICAL impact
- Nodes lost: 1
- Edges lost: 1,247
- Connectivity: Broken
- Alternative paths: Available for 89% of routes
```

## 🧪 Testing

```bash
# Run comprehensive tests
python test_app.py

# Expected output:
# ✅ Data loading: 7,698 airports, 66,315 routes
# ✅ Graph building: 7,698 nodes, 36,588 edges
# ✅ Shortest path algorithm working
# ✅ Hub analysis working
# ✅ All imports successful
```

## 📊 Performance

- **Data Size**: 7,698 airports, 66,315 routes
- **Graph Size**: 7,698 nodes, 36,588 edges
- **Processing Time**: ~30 seconds for full pipeline
- **Memory Usage**: ~500MB for full dataset
- **Response Time**: <2 seconds for route queries

## 🔧 Troubleshooting

### Common Issues
1. **Data not found**: Run `python -m pipeline.main_pipeline` first
2. **Import errors**: Ensure virtual environment is activated
3. **Memory issues**: Reduce dataset size in pipeline
4. **Map not loading**: Check Folium installation

### Debug Mode
```bash
# Streamlit debug
streamlit run app/streamlit_app.py --logger.level debug

# Pipeline debug
python -m pipeline.main_pipeline --verbose
```

## 📈 Future Enhancements

- [ ] Real-time flight data integration
- [ ] Advanced filtering and search
- [ ] Export functionality (PDF, CSV)
- [ ] Multi-language support
- [ ] API endpoints for external integration
- [ ] Machine learning route optimization
- [ ] Environmental impact analysis

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Powered by**: Python, NetworkX, Streamlit, Folium, Gephi
**Data Source**: OpenFlights Dataset
**Last Updated**: 2024
