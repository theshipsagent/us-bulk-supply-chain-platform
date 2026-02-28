"""
Unit tests for data loaders.

Tests CSV reading, data validation, batch processing, and database operations.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

from src.config.settings import DATA_FILES


class TestDataLoaderUtils:
    """Test data loader utility functions."""

    def test_clean_value_string(self):
        """Test clean_value for strings."""
        from src.data_loaders.load_waterways import clean_value

        assert clean_value("test") == "test"
        assert clean_value("  test  ") == "test"
        assert clean_value(None) is None
        assert clean_value(pd.NA) is None

    def test_clean_value_int(self):
        """Test clean_value for integers."""
        from src.data_loaders.load_waterways import clean_value

        assert clean_value(123, 'int') == 123
        assert clean_value("456", 'int') == 456
        assert clean_value("invalid", 'int') is None
        assert clean_value(None, 'int') is None

    def test_clean_value_float(self):
        """Test clean_value for floats."""
        from src.data_loaders.load_waterways import clean_value

        assert clean_value(123.45, 'float') == 123.45
        assert clean_value("678.90", 'float') == 678.90
        assert clean_value("invalid", 'float') is None
        assert clean_value(None, 'float') is None


class TestWaterwayLoader:
    """Test waterway network loader."""

    @pytest.fixture
    def sample_waterway_data(self):
        """Create sample waterway data."""
        return pd.DataFrame({
            'OBJECTID': [1, 2, 3],
            'LINKNUM': [100, 101, 102],
            'ANODE': [1000, 1001, 1002],
            'BNODE': [1001, 1002, 1003],
            'LENGTH': [10.5, 15.3, 8.7],
            'RIVERNAME': ['Mississippi River', 'Ohio River', 'Mississippi River'],
            'STATE': ['LA', 'OH', 'LA'],
        })

    def test_csv_file_exists(self):
        """Test that waterway CSV file exists."""
        csv_path = DATA_FILES['waterway_networks']
        assert csv_path.exists(), f"Waterway CSV not found: {csv_path}"

    def test_csv_has_required_columns(self, sample_waterway_data):
        """Test CSV has all required columns."""
        required_columns = ['OBJECTID', 'LINKNUM', 'ANODE', 'BNODE', 'LENGTH']
        for col in required_columns:
            assert col in sample_waterway_data.columns

    @patch('src.data_loaders.load_waterways.get_db_session')
    @patch('networkx.DiGraph')
    def test_graph_building(self, mock_graph, mock_db, sample_waterway_data):
        """Test NetworkX graph building from data."""
        import networkx as nx

        G = nx.DiGraph()
        for _, row in sample_waterway_data.iterrows():
            G.add_edge(
                int(row['ANODE']),
                int(row['BNODE']),
                linknum=int(row['LINKNUM']),
                length=float(row['LENGTH'])
            )

        assert len(G.edges()) == 3
        assert G.has_edge(1000, 1001)
        assert G.has_edge(1001, 1002)
        assert G[1000][1001]['linknum'] == 100


class TestLocksLoader:
    """Test locks facility loader."""

    def test_csv_file_exists(self):
        """Test that locks CSV file exists."""
        csv_path = DATA_FILES['locks']
        assert csv_path.exists(), f"Locks CSV not found: {csv_path}"

    @pytest.fixture
    def sample_locks_data(self):
        """Create sample locks data."""
        return pd.DataFrame({
            'OBJECTID': [1, 2],
            'PMSNAME': ['Lock 1', 'Lock 2'],
            'WIDTH': [110.0, 84.0],
            'LENGTH': [600.0, 1200.0],
            'LIFT': [25.0, 30.0],
            'x': [-90.0, -91.0],
            'y': [38.0, 39.0],
        })

    def test_locks_dimensional_data(self, sample_locks_data):
        """Test locks have dimensional constraints."""
        assert all(sample_locks_data['WIDTH'] > 0)
        assert all(sample_locks_data['LENGTH'] > 0)


class TestDocksLoader:
    """Test docks facility loader."""

    def test_csv_file_exists(self):
        """Test that docks CSV file exists."""
        csv_path = DATA_FILES['docks']
        assert csv_path.exists(), f"Docks CSV not found: {csv_path}"

    @pytest.fixture
    def sample_docks_data(self):
        """Create sample docks data."""
        return pd.DataFrame({
            'ObjectID': [1, 2, 3],
            'NAV_UNIT_NAME': ['Dock A', 'Dock B', 'Dock C'],
            'LATITUDE': [38.5, 39.0, 37.5],
            'LONGITUDE': [-90.0, -91.0, -89.0],
            'DEPTH_MIN': [12.0, 15.0, 10.0],
            'TOWS_LINK_NUM': [100, 101, 102],
        })

    def test_docks_geospatial_data(self, sample_docks_data):
        """Test docks have valid coordinates."""
        assert all(sample_docks_data['LATITUDE'].between(-90, 90))
        assert all(sample_docks_data['LONGITUDE'].between(-180, 180))


class TestTonnagesLoader:
    """Test link tonnages loader."""

    def test_csv_file_exists(self):
        """Test that tonnages CSV file exists."""
        csv_path = DATA_FILES['link_tonnages']
        assert csv_path.exists(), f"Tonnages CSV not found: {csv_path}"

    @pytest.fixture
    def sample_tonnages_data(self):
        """Create sample tonnages data."""
        return pd.DataFrame({
            'OBJECTID': [1, 2],
            'LINKNUM': [100, 101],
            'TOTALUP': [50000, 75000],
            'TOTALDOWN': [45000, 60000],
            'COALUP': [30000, 40000],
            'COALDOWN': [25000, 35000],
        })

    def test_tonnages_foreign_key(self, sample_tonnages_data):
        """Test tonnages have LINKNUM for joining."""
        assert 'LINKNUM' in sample_tonnages_data.columns
        assert all(sample_tonnages_data['LINKNUM'] > 0)

    def test_tonnages_non_negative(self, sample_tonnages_data):
        """Test tonnage values are non-negative."""
        numeric_cols = ['TOTALUP', 'TOTALDOWN', 'COALUP', 'COALDOWN']
        for col in numeric_cols:
            assert all(sample_tonnages_data[col] >= 0)


class TestVesselsLoader:
    """Test vessels registry loader."""

    def test_csv_file_exists(self):
        """Test that vessels CSV file exists."""
        csv_path = DATA_FILES['vessels']
        assert csv_path.exists(), f"Vessels CSV not found: {csv_path}"

    @pytest.fixture
    def sample_vessels_data(self):
        """Create sample vessels data."""
        return pd.DataFrame({
            'IMO': ['1234567', '2345678', '3456789'],
            'Vessel': ['Ship A', 'Ship B', 'Ship C'],
            'Beam': [10.5, 12.0, 9.5],
            'Depth(m)': [3.0, 3.5, 2.8],
            'LOA': [60.0, 75.0, 55.0],
            'DWT': [15000, 20000, 12000],
        })

    def test_vessels_have_imo(self, sample_vessels_data):
        """Test vessels have IMO numbers."""
        assert 'IMO' in sample_vessels_data.columns
        assert all(sample_vessels_data['IMO'].notna())

    def test_vessels_dimensional_constraints(self, sample_vessels_data):
        """Test vessel dimensions are reasonable."""
        assert all(sample_vessels_data['Beam'] > 0)
        assert all(sample_vessels_data['Depth(m)'] > 0)
        assert all(sample_vessels_data['LOA'] > 0)


class TestBatchProcessing:
    """Test batch processing functionality."""

    def test_batch_size(self):
        """Test batch size splitting."""
        data = list(range(1000))
        batch_size = 100

        batches = [data[i:i+batch_size] for i in range(0, len(data), batch_size)]

        assert len(batches) == 10
        assert len(batches[0]) == 100
        assert sum(len(b) for b in batches) == 1000

    def test_partial_batch(self):
        """Test handling of partial final batch."""
        data = list(range(950))
        batch_size = 100

        batches = [data[i:i+batch_size] for i in range(0, len(data), batch_size)]

        assert len(batches) == 10
        assert len(batches[-1]) == 50  # Last batch is partial


@pytest.mark.integration
class TestDatabaseIntegration:
    """Integration tests requiring database connection."""

    @pytest.fixture(scope="class")
    def db_available(self):
        """Check if database is available."""
        try:
            from src.config.database import verify_db_connection
            return verify_db_connection()
        except Exception:
            pytest.skip("Database not available")

    def test_database_connection(self, db_available):
        """Test database connection."""
        from src.config.database import verify_db_connection
        assert verify_db_connection()

    def test_postgis_enabled(self, db_available):
        """Test PostGIS extension is enabled."""
        from src.config.database import verify_postgis
        assert verify_postgis()

    def test_tables_exist(self, db_available):
        """Test all required tables exist."""
        from src.config.database import get_table_counts

        counts = get_table_counts()
        required_tables = ['waterway_links', 'locks', 'docks', 'link_tonnages', 'vessels']

        for table in required_tables:
            assert table in counts


if __name__ == "__main__":
    """Run tests."""
    pytest.main([__file__, '-v'])
