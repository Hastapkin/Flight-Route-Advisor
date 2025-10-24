"""
Test script for Flight Route Advisor application
Tests data loading and basic functionality
"""

import sys
from pathlib import Path
import pandas as pd

# Add pipeline to path
sys.path.append(str(Path(__file__).parent))

def test_data_loading():
    """Test if data files exist and can be loaded"""
    print("Testing data loading...")
    
    data_dir = Path("data/cleaned")
    required_files = [
        "airports_cleaned.csv",
        "airlines_cleaned.csv",
        "routes_graph.csv"
    ]
    
    # Check if files exist
    for file in required_files:
        file_path = data_dir / file
        if file_path.exists():
            print(f"[OK] {file} exists")
        else:
            print(f"[ERROR] {file} not found")
            return False
    
    # Test loading data
    try:
        airports_df = pd.read_csv(data_dir / "airports_cleaned.csv")
        routes_df = pd.read_csv(data_dir / "routes_graph.csv")
        
        print(f"[OK] Airports loaded: {len(airports_df)} rows")
        print(f"[OK] Routes loaded: {len(routes_df)} rows")
        
        # Check required columns
        required_airport_cols = ['airport_id', 'iata', 'name', 'city', 'country', 'latitude', 'longitude']
        required_route_cols = ['source_airport_id', 'destination_airport_id', 'distance_km']
        
        missing_airport_cols = [col for col in required_airport_cols if col not in airports_df.columns]
        missing_route_cols = [col for col in required_route_cols if col not in routes_df.columns]
        
        if missing_airport_cols:
            print(f"[ERROR] Missing airport columns: {missing_airport_cols}")
            return False
        
        if missing_route_cols:
            print(f"[ERROR] Missing route columns: {missing_route_cols}")
            return False
        
        print("[OK] All required columns present")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error loading data: {e}")
        return False


def test_graph_analyzer():
    """Test graph analyzer functionality"""
    print("\nTesting graph analyzer...")
    
    try:
        from pipeline.graph_analyzer import create_flight_analyzer
        
        analyzer = create_flight_analyzer("data/cleaned")
        print("[OK] Graph analyzer created successfully")
        
        # Test network stats
        stats = analyzer.get_network_stats()
        print(f"[OK] Network stats: {stats['total_nodes']} nodes, {stats['total_edges']} edges")
        
        # Test shortest path (if possible)
        try:
            # Get some airports for testing
            airports_df = analyzer.airports_df
            test_airports = airports_df[airports_df['iata'].notna()]['iata'].head(5).tolist()
            
            if len(test_airports) >= 2:
                result = analyzer.find_shortest_path(test_airports[0], test_airports[1])
                if "error" not in result:
                    print(f"[OK] Shortest path test: {test_airports[0]} -> {test_airports[1]}")
                else:
                    print(f"[WARNING] Shortest path test failed: {result['error']}")
        except Exception as e:
            print(f"[WARNING] Shortest path test error: {e}")
        
        # Test hub analysis
        try:
            hub_result = analyzer.analyze_hubs(None, 5)
            if "error" not in hub_result:
                print(f"[OK] Hub analysis: {len(hub_result['top_hubs'])} top hubs")
            else:
                print(f"[WARNING] Hub analysis failed: {hub_result['error']}")
        except Exception as e:
            print(f"[WARNING] Hub analysis error: {e}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Graph analyzer error: {e}")
        return False


def test_streamlit_imports():
    """Test if Streamlit and related packages can be imported"""
    print("\nTesting Streamlit imports...")
    
    try:
        import streamlit as st
        print("[OK] Streamlit imported")
        
        import folium
        print("[OK] Folium imported")
        
        import streamlit_folium
        print("[OK] Streamlit-Folium imported")
        
        import networkx as nx
        print("[OK] NetworkX imported")
        
        return True
        
    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        return False


def main():
    """Run all tests"""
    print("Flight Route Advisor - Testing Application")
    print("=" * 50)
    
    tests = [
        test_data_loading,
        test_streamlit_imports,
        test_graph_analyzer
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed! Application is ready to run.")
        print("\nTo start the application, run:")
        print("   python run_app.py")
    else:
        print("Some tests failed. Please check the errors above.")
        print("\nTo fix issues:")
        print("   1. Run the pipeline: python -m pipeline.main_pipeline")
        print("   2. Install missing packages: pip install -r requirements.txt")


if __name__ == "__main__":
    main()
