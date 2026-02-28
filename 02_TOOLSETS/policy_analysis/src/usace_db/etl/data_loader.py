"""
Data loader - loads operators and vessels into DuckDB.
"""
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class DataLoader:
    """Loads operator and vessel data into DuckDB."""

    def __init__(self, db_connection, batch_size=5000):
        """
        Initialize data loader.

        Args:
            db_connection: DatabaseConnection instance
            batch_size: Number of records per batch insert
        """
        self.db = db_connection
        self.batch_size = batch_size

    def load_operators(self, operators_df):
        """
        Load operators into database.

        Args:
            operators_df: DataFrame with operator data

        Returns:
            int: Number of operators loaded
        """
        logger.info(f"Loading {len(operators_df)} operators...")

        # Map DataFrame columns to database columns (handles both old and new formats)
        column_mapping = {
            'ts_oper': 'ts_oper',
            'name': 'operator_name',
            'dba': 'dba',
            'poc': 'poc',
            'address': 'address',
            'city': 'city',
            'state': 'state',
            'zip': 'zip',
            'area': 'area',
            'phone': 'phone',
            'dist': 'dist_code',
            'series': 'series_code',
            'service': 'service_code',
            'princ_comm': 'principal_commodity',
            'point_loc': 'point_of_location',
            # Vessel count columns (old and new formats)
            'dbc': 'count_dbc',  # Old format: DBC
            'cs': 'count_cs',
            'gcc': 'count_gcc',
            'sc': 'count_sc',
            'tan': 'count_tan',
            'push': 'count_push',
            'tug': 'count_tug',
            'pass': 'count_pass',
            'osv': 'count_osv',
            'dcb': 'count_dcb',  # New format: DCB
            'dob': 'count_dob',
            'db': 'count_db',
            'lsb': 'count_lsb',
            'ody': 'count_ody',
            'shtb': 'count_shtb',
            'dhtb': 'count_dhtb',
            'otb': 'count_otb',
            'fl_yr': 'fleet_year'
        }

        # Rename columns
        df = operators_df.rename(columns=column_mapping)

        # Use DuckDB's native DataFrame insert (specify columns to exclude created_at)
        try:
            # Get column names from DataFrame
            cols = ', '.join(df.columns.tolist())

            # DuckDB can insert directly from pandas DataFrame
            self.db.conn.register('temp_operators', df)
            self.db.conn.execute(f"""
                INSERT INTO operators ({cols})
                SELECT * FROM temp_operators
            """)
            self.db.conn.unregister('temp_operators')

            logger.info(f"✓ Loaded {len(df)} operators")
            return len(df)

        except Exception as e:
            logger.error(f"Failed to load operators: {e}")
            raise

    def load_vessels(self, vessels_df):
        """
        Load vessels into database.

        Args:
            vessels_df: DataFrame with vessel data

        Returns:
            int: Number of vessels loaded
        """
        logger.info(f"Loading {len(vessels_df)} vessels...")

        # Map DataFrame columns to database columns (handles both old and new formats)
        column_mapping = {
            'vessel': 'vessel_id',
            'vs_name': 'vessel_name',
            'vs_number': 'vs_number',
            'cg_number': 'cg_number',
            'vtcc': 'vtcc_code',
            'icst': 'icst_code',
            'nrt': 'nrt',
            'hp': 'horsepower',     # New format
            'hrp': 'horsepower',    # Old format (2013-2014)
            'reg_lngth': 'reg_length',
            'over_lngth': 'over_length',
            'reg_brdth': 'reg_breadth',
            'over_brdth': 'over_breadth',
            'hfp': 'hfp',
            'cap_ref': 'cap_ref_code',
            'cap_pass': 'cap_pass',
            'cap_tons': 'cap_tons',
            'year': 'year_built',
            'reblt': 'is_rebuilt',
            'year_rebuilt': 'year_rebuilt',
            'year_vessel': 'year_vessel',
            'load_draft': 'load_draft',
            'light_draft': 'light_draft',
            'equip1': 'equip1',
            'equip2': 'equip2',
            'state': 'state',
            'base1': 'base1',
            'base2': 'base2',
            'region': 'region_code',  # New format
            'series': 'region_code',  # Old format (2013-2014) - series was used instead of region
            'ts_oper': 'ts_oper',
            'fl_yr': 'fleet_year'
        }

        # Rename columns
        df = vessels_df.rename(columns=column_mapping)

        # Convert REBLT field to boolean
        if 'is_rebuilt' in df.columns:
            df['is_rebuilt'] = df['is_rebuilt'].apply(
                lambda x: True if x in ['Y', '*'] else False
            )

        # Add source file tracking
        df['source_file'] = 'TS23VS'

        # Use DuckDB's native DataFrame insert (batched for progress updates)
        try:
            # Get column names from DataFrame
            cols = ', '.join(df.columns.tolist())

            total_loaded = 0
            for i in range(0, len(df), self.batch_size):
                batch = df.iloc[i:i+self.batch_size]

                # Register temp DataFrame and insert
                self.db.conn.register('temp_vessels', batch)
                self.db.conn.execute(f"""
                    INSERT INTO vessels ({cols})
                    SELECT * FROM temp_vessels
                """)
                self.db.conn.unregister('temp_vessels')

                total_loaded += len(batch)
                logger.info(f"  Loaded {total_loaded:,} / {len(df):,} vessels...")

            logger.info(f"✓ Loaded {total_loaded:,} vessels")
            return total_loaded

        except Exception as e:
            logger.error(f"Failed to load vessels: {e}")
            raise

    def refresh_materialized_view(self):
        """Refresh the vessel_analytics_view (DuckDB views are automatically updated)."""
        logger.info("DuckDB views are automatically updated - no refresh needed")
        # In DuckDB, regular views are dynamic and don't need refreshing
        # The schema will create it as a regular view
        return True

    def get_statistics(self):
        """Get database statistics after loading."""
        stats = {}

        # Count operators
        result = self.db.conn.execute("SELECT COUNT(*) FROM operators").fetchone()
        stats['operators'] = result[0]

        # Count vessels
        result = self.db.conn.execute("SELECT COUNT(*) FROM vessels").fetchone()
        stats['vessels'] = result[0]

        # Count by vessel type
        result = self.db.conn.execute("""
            SELECT vtcc.vessel_type, COUNT(*) as count
            FROM vessels v
            LEFT JOIN lookup_vtcc vtcc ON v.vtcc_code = vtcc.vtcc_code
            GROUP BY vtcc.vessel_type
            ORDER BY count DESC
            LIMIT 10
        """).fetchall()
        stats['top_vessel_types'] = result

        # Count by district
        result = self.db.conn.execute("""
            SELECT d.district_name, COUNT(DISTINCT v.vessel_id) as count
            FROM operators o
            LEFT JOIN vessels v ON o.ts_oper = v.ts_oper
            LEFT JOIN lookup_district d ON o.dist_code = d.dist_code
            WHERE d.district_name IS NOT NULL
            GROUP BY d.district_name
            ORDER BY count DESC
            LIMIT 10
        """).fetchall()
        stats['top_districts'] = result

        return stats
