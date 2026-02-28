"""
Basic network validation tests
"""

import unittest
import networkx as nx
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent / 'src'))

from network.graph_builder import RailNetworkGraph


class TestNetworkGraph(unittest.TestCase):
    
    def test_graph_creation(self):
        """Test that graph can be created."""
        builder = RailNetworkGraph()
        self.assertIsNotNone(builder.graph)
        self.assertIsInstance(builder.graph, nx.MultiDiGraph)
    
    def test_haversine_calculation(self):
        """Test haversine distance calculation."""
        from shapely.geometry import LineString
        
        builder = RailNetworkGraph()
        # Line from NYC to Philadelphia (approx 80 miles)
        line = LineString([(-74.006, 40.7128), (-75.1652, 39.9526)])
        
        miles = builder._calculate_length_miles(line)
        self.assertGreater(miles, 70)
        self.assertLess(miles, 100)


if __name__ == '__main__':
    unittest.main()
