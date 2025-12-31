# Flight Route Advisor
## Quick Start

### 1. Set up
```bash
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
# 1. Process data (run notebook first)
#    Open and run notebook/flight_route.ipynb to generate cleaned data

# 2. Start web app
streamlit run app/streamlit_app.py
```

## Project Structure

```
Flight-Route-Advisor/
|-- app/
|   `-- streamlit_app.py          # Interactive web application
|-- pipeline/
|   `-- graph_analyzer.py          # Network graph analysis and route finding
|-- notebook/
|   `-- flight_route.ipynb        # Gephi export & analysis
|-- data/
|   |-- cleaned/                  # Processed CSV files
|   `-- gephi/                    # Gephi visualization files
|-- requirements.txt           # Python dependencies
|-- run_app.py                # Application launcher
```

## Usage Examples

### Find Shortest Route
```python
# In Streamlit app
Source: SGN (Ho Chi Minh City)
Destination: LHR (London Heathrow)
Result: SGN -> DXB -> LHR (2 stops, 10,432 km)
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

## Performance

- **Data Size**: 7,698 airports, 66,315 routes
- **Graph Size**: 7,698 nodes, 36,588 edges
- **Processing Time**: ~30 seconds for full pipeline
- **Memory Usage**: ~500MB for full dataset
- **Response Time**: <2 seconds for route queries

## Future Enhancements

- [ ] Real-time flight data integration
- [ ] Advanced filtering and search
- [ ] Export functionality (PDF, CSV)
- [ ] Multi-language support
- [ ] API endpoints for external integration
- [ ] Machine learning route optimization
- [ ] Environmental impact analysis

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---