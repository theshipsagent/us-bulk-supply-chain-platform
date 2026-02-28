"""
Code loader - populates lookup tables from code_mappings.yaml
"""
import yaml
import logging

logger = logging.getLogger(__name__)


class CodeLoader:
    """Loads code mappings into lookup tables."""

    def __init__(self, db_connection, code_mappings_file):
        """
        Initialize code loader.

        Args:
            db_connection: DatabaseConnection instance
            code_mappings_file: Path to code_mappings.yaml
        """
        self.db = db_connection
        self.code_mappings_file = code_mappings_file
        self.mappings = None

    def load_mappings(self):
        """Load code mappings from YAML file."""
        try:
            with open(self.code_mappings_file, 'r', encoding='utf-8') as f:
                self.mappings = yaml.safe_load(f)
            logger.info(f"Loaded code mappings from: {self.code_mappings_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to load code mappings: {e}")
            return False

    def populate_vtcc_codes(self):
        """Populate lookup_vtcc table."""
        if not self.mappings:
            self.load_mappings()

        vtcc_codes = self.mappings.get('vtcc_codes', {})
        logger.info(f"Populating {len(vtcc_codes)} VTCC codes...")

        for code, data in vtcc_codes.items():
            self.db.conn.execute("""
                INSERT OR IGNORE INTO lookup_vtcc
                (vtcc_code, construction_type, vessel_type, characteristic_desc,
                 is_self_propelled, is_barge)
                VALUES (?)
            """, [
                code,
                data['construction_type'],
                data['vessel_type'],
                data['characteristic_desc'],
                data['is_self_propelled'],
                data['is_barge']
            ])

        logger.info(f"✓ VTCC codes populated")

    def populate_icst_codes(self):
        """Populate lookup_icst table."""
        if not self.mappings:
            self.load_mappings()

        icst_codes = self.mappings.get('icst_codes', {})
        logger.info(f"Populating {len(icst_codes)} ICST codes...")

        
            for code, data in icst_codes.items():
                self.db.conn.execute("""
                    INSERT OR IGNORE INTO lookup_icst (icst_code, description, category)
                    VALUES (?)
                    
                """), {
                    'code': code,
                    'desc': data['description'],
                    'category': data['category']
                })

        logger.info(f"✓ ICST codes populated")

    def populate_districts(self):
        """Populate lookup_district table."""
        if not self.mappings:
            self.load_mappings()

        districts = self.mappings.get('districts', {})
        logger.info(f"Populating {len(districts)} district codes...")

        
            for code, data in districts.items():
                self.db.conn.execute("""
                    INSERT OR IGNORE INTO lookup_district
                    (dist_code, district_name, district_abbr, region, state, city)
                    VALUES (?)
                    
                """), {
                    'code': code,
                    'name': data['district_name'],
                    'abbr': data['district_abbr'],
                    'region': data['region'],
                    'state': data['state'],
                    'city': data['city']
                })

        logger.info(f"✓ District codes populated")

    def populate_series(self):
        """Populate lookup_series table."""
        if not self.mappings:
            self.load_mappings()

        series = self.mappings.get('series', {})
        logger.info(f"Populating {len(series)} series codes...")

        
            for code, data in series.items():
                self.db.conn.execute("""
                    INSERT OR IGNORE INTO lookup_series (series_code, series_name, description)
                    VALUES (?)
                    
                """), {
                    'code': code,
                    'name': data['series_name'],
                    'desc': data['description']
                })

        logger.info(f"✓ Series codes populated")

    def populate_service_types(self):
        """Populate lookup_service table."""
        if not self.mappings:
            self.load_mappings()

        service_types = self.mappings.get('service_types', {})
        logger.info(f"Populating {len(service_types)} service type codes...")

        
            for code, data in service_types.items():
                self.db.conn.execute("""
                    INSERT OR IGNORE INTO lookup_service
                    (service_code, service_name, description, is_for_hire, regulatory_status)
                    VALUES (?)
                    
                """), {
                    'code': code,
                    'name': data['service_name'],
                    'desc': data['description'],
                    'for_hire': data['is_for_hire'],
                    'status': data['regulatory_status']
                })

        logger.info(f"✓ Service type codes populated")

    def populate_capacity_ref(self):
        """Populate lookup_capacity_ref table."""
        if not self.mappings:
            self.load_mappings()

        capacity_ref = self.mappings.get('capacity_ref', {})
        logger.info(f"Populating {len(capacity_ref)} capacity reference codes...")

        
            for code, data in capacity_ref.items():
                self.db.conn.execute("""
                    INSERT OR IGNORE INTO lookup_capacity_ref
                    (cap_ref_code, description, cargo_type)
                    VALUES (?)
                    
                """), {
                    'code': code if code else '',  # Handle empty string for "general bulk"
                    'desc': data['description'],
                    'cargo_type': data['cargo_type']
                })

        logger.info(f"✓ Capacity reference codes populated")

    def populate_equipment_types(self):
        """Populate lookup_equipment table."""
        if not self.mappings:
            self.load_mappings()

        equipment = self.mappings.get('equipment_types', {})
        logger.info(f"Populating {len(equipment)} equipment type codes...")

        
            for code, data in equipment.items():
                self.db.conn.execute("""
                    INSERT OR IGNORE INTO lookup_equipment
                    (equipment_code, equipment_name, category, description)
                    VALUES (?)
                    
                """), {
                    'code': code,
                    'name': data['equipment_name'],
                    'category': data['category'],
                    'desc': data['description']
                })

        logger.info(f"✓ Equipment type codes populated")

    def populate_all_codes(self):
        """Populate all lookup tables."""
        logger.info("=" * 60)
        logger.info("Populating all lookup tables...")
        logger.info("=" * 60)

        self.populate_vtcc_codes()
        self.populate_icst_codes()
        self.populate_districts()
        self.populate_series()
        self.populate_service_types()
        self.populate_capacity_ref()
        self.populate_equipment_types()

        logger.info("=" * 60)
        logger.info("✓ All lookup tables populated successfully")
        logger.info("=" * 60)
