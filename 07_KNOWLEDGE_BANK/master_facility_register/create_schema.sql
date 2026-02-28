-- MASTER FACILITY REGISTER — DuckDB Schema
-- Database: facility_master.duckdb
-- Purpose: Unified facility intelligence linking fragmented data sources
-- Created: 2026-02-23

-- ============================================================================
-- TABLE: facilities
-- Purpose: Master facility inventory (one row per facility)
-- ============================================================================

CREATE TABLE IF NOT EXISTS facilities (
    -- Master identifiers
    facility_master_id VARCHAR PRIMARY KEY,     -- e.g., "MFR_00012345"
    canonical_name VARCHAR NOT NULL,            -- "ArcelorMittal Burns Harbor"
    facility_type VARCHAR,                      -- "steel_mill", "cement_plant", "power_plant"
    naics_primary INTEGER,                      -- Primary NAICS code

    -- Location (master coordinates - weighted centroid of all sub-facilities)
    latitude DOUBLE,
    longitude DOUBLE,
    state VARCHAR(2),
    county VARCHAR,
    city VARCHAR,
    zip_code VARCHAR(10),

    -- Geospatial (WKT format for geometry)
    boundary_geom VARCHAR,                      -- Facility property boundary polygon (WKT)

    -- Operational status
    status VARCHAR,                             -- "active", "idle", "closed", "under_construction"
    first_observed_date DATE,                   -- Earliest date in any data source
    closure_date DATE,                          -- If closed
    closure_reason VARCHAR,                     -- "retirement", "bankruptcy", "consolidation"

    -- Capacity & Scale
    annual_capacity_tons DOUBLE,                -- Production capacity (if applicable)
    annual_capacity_unit VARCHAR,               -- "tons_cement", "tons_steel", "mw_electric"
    employment_count INTEGER,                   -- From BLS or company reports
    land_area_acres DOUBLE,                     -- From county parcel data

    -- Ownership
    parent_company_id VARCHAR,                  -- Link to company_master in Knowledge Bank
    operator_company_id VARCHAR,                -- May differ from owner (contract operator)

    -- Data provenance
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP,
    data_quality_score DOUBLE,                  -- Confidence in entity resolution (0.0-1.0)
    notes TEXT                                  -- Free-form notes
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_facilities_state ON facilities(state);
CREATE INDEX IF NOT EXISTS idx_facilities_naics ON facilities(naics_primary);
CREATE INDEX IF NOT EXISTS idx_facilities_status ON facilities(status);
CREATE INDEX IF NOT EXISTS idx_facilities_parent ON facilities(parent_company_id);
CREATE INDEX IF NOT EXISTS idx_facilities_type ON facilities(facility_type);

-- ============================================================================
-- TABLE: facility_external_ids
-- Purpose: Cross-reference table linking external database IDs to master facility
-- ============================================================================

CREATE TABLE IF NOT EXISTS facility_external_ids (
    facility_master_id VARCHAR,                 -- Links to facilities table
    source_system VARCHAR,                      -- "epa_frs", "rail_scrs", "port_unloc", "panjiva"
    external_id VARCHAR,                        -- ID from source system
    external_name VARCHAR,                      -- Name as it appears in source system
    match_confidence DOUBLE,                    -- How confident is this link? (0.0-1.0)
    verified_by VARCHAR,                        -- "automated" or "manual_review"
    verified_date DATE,
    notes TEXT,
    PRIMARY KEY (facility_master_id, source_system, external_id),
    FOREIGN KEY (facility_master_id) REFERENCES facilities(facility_master_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_external_ids_source ON facility_external_ids(source_system);
CREATE INDEX IF NOT EXISTS idx_external_ids_external ON facility_external_ids(external_id);

-- ============================================================================
-- TABLE: facility_attributes
-- Purpose: All attributes from all sources (key-value store)
-- Allows flexible attribute storage without schema changes
-- ============================================================================

CREATE TABLE IF NOT EXISTS facility_attributes (
    facility_master_id VARCHAR,                 -- Links to facilities table
    attribute_category VARCHAR,                 -- "environmental", "rail", "port", "employment"
    attribute_key VARCHAR,                      -- "air_permit_number", "rail_connections", "berth_count"
    attribute_value VARCHAR,                    -- The actual value
    attribute_value_numeric DOUBLE,             -- Numeric value if applicable
    attribute_unit VARCHAR,                     -- Unit of measure
    source_system VARCHAR,                      -- Where this data came from
    as_of_date DATE,                            -- When this was true
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    PRIMARY KEY (facility_master_id, attribute_category, attribute_key, source_system),
    FOREIGN KEY (facility_master_id) REFERENCES facilities(facility_master_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_attributes_category ON facility_attributes(attribute_category);
CREATE INDEX IF NOT EXISTS idx_attributes_key ON facility_attributes(attribute_key);
CREATE INDEX IF NOT EXISTS idx_attributes_source ON facility_attributes(source_system);

-- ============================================================================
-- TABLE: facility_infrastructure
-- Purpose: Rail, port, road, pipeline connections
-- ============================================================================

CREATE TABLE IF NOT EXISTS facility_infrastructure (
    facility_master_id VARCHAR,                 -- Links to facilities table
    infrastructure_type VARCHAR,                -- "rail", "port", "road", "pipeline"
    connection_name VARCHAR,                    -- "Canadian National", "Port of Indiana-Burns Harbor"
    connection_id VARCHAR,                      -- External ID if available (e.g., SCRS code, UNLOC)
    latitude DOUBLE,                            -- Location of connection point
    longitude DOUBLE,
    capacity VARCHAR,                           -- "1200 car storage", "3 berths", "max 1000ft LOA"
    operational_status VARCHAR,                 -- "active", "idle", "under_construction"
    source_system VARCHAR,
    as_of_date DATE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (facility_master_id) REFERENCES facilities(facility_master_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_infrastructure_type ON facility_infrastructure(infrastructure_type);
CREATE INDEX IF NOT EXISTS idx_infrastructure_facility ON facility_infrastructure(facility_master_id);

-- ============================================================================
-- TABLE: facility_ownership_history
-- Purpose: Track ownership changes, M&A, consolidation
-- ============================================================================

CREATE TABLE IF NOT EXISTS facility_ownership_history (
    facility_master_id VARCHAR,                 -- Links to facilities table
    effective_date DATE,                        -- When ownership changed
    previous_owner_id VARCHAR,                  -- Company master ID (old owner)
    new_owner_id VARCHAR,                       -- Company master ID (new owner)
    transaction_type VARCHAR,                   -- "acquisition", "merger", "divestiture", "bankruptcy"
    transaction_value_usd DOUBLE,               -- Deal value if known
    source_url VARCHAR,                         -- Press release, SEC filing, etc.
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (facility_master_id) REFERENCES facilities(facility_master_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_ownership_facility ON facility_ownership_history(facility_master_id);
CREATE INDEX IF NOT EXISTS idx_ownership_date ON facility_ownership_history(effective_date);

-- ============================================================================
-- VIEW: facility_summary
-- Purpose: Quick summary of facility with external IDs
-- ============================================================================

CREATE OR REPLACE VIEW facility_summary AS
SELECT
    f.facility_master_id,
    f.canonical_name,
    f.facility_type,
    f.naics_primary,
    f.state,
    f.city,
    f.status,
    f.annual_capacity_tons,
    f.employment_count,
    f.parent_company_id,
    f.data_quality_score,
    COUNT(DISTINCT e.source_system) AS external_source_count,
    STRING_AGG(DISTINCT e.source_system || ':' || e.external_id, '; ') AS external_ids
FROM facilities f
LEFT JOIN facility_external_ids e ON f.facility_master_id = e.facility_master_id
GROUP BY
    f.facility_master_id,
    f.canonical_name,
    f.facility_type,
    f.naics_primary,
    f.state,
    f.city,
    f.status,
    f.annual_capacity_tons,
    f.employment_count,
    f.parent_company_id,
    f.data_quality_score;

-- ============================================================================
-- SAMPLE DATA (for testing)
-- ============================================================================

-- Example facility: ArcelorMittal Burns Harbor
INSERT INTO facilities (
    facility_master_id, canonical_name, facility_type, naics_primary,
    latitude, longitude, state, county, city, zip_code,
    status, annual_capacity_tons, annual_capacity_unit, employment_count, land_area_acres,
    parent_company_id, data_quality_score, notes
) VALUES (
    'MFR_00000001',
    'ArcelorMittal Burns Harbor',
    'steel_mill',
    331110,
    41.6289,
    -87.1347,
    'IN',
    'Porter County',
    'Portage',
    '46368',
    'active',
    5000000,
    'tons_steel',
    3800,
    850,
    'ARCELORMITTAL_GROUP',
    0.96,
    'Integrated steel mill (blast furnace); primary GGBFS source in US Midwest'
);

-- External IDs for ArcelorMittal Burns Harbor
INSERT INTO facility_external_ids (
    facility_master_id, source_system, external_id, external_name, match_confidence, verified_by
) VALUES
    ('MFR_00000001', 'epa_frs', 'FIN000004359', 'ARCELORMITTAL BURNS HARBOR', 0.98, 'automated'),
    ('MFR_00000001', 'rail_scrs', '045802', 'Burns Harbor Works', 0.95, 'manual_review'),
    ('MFR_00000001', 'port_unloc', 'USBUR', 'Port of Indiana-Burns Harbor', 0.92, 'automated'),
    ('MFR_00000001', 'eia', '50000', 'Burns Harbor Energy Center', 1.00, 'manual_review');

-- Sample attributes
INSERT INTO facility_attributes (
    facility_master_id, attribute_category, attribute_key, attribute_value, source_system
) VALUES
    ('MFR_00000001', 'environmental', 'air_permit_number', 'IN0000451', 'epa_frs'),
    ('MFR_00000001', 'rail', 'rail_connections', 'CN, CSX, NS', 'rail_scrs'),
    ('MFR_00000001', 'rail', 'car_storage_capacity', '1200', 'rail_scrs'),
    ('MFR_00000001', 'port', 'berth_count', '3', 'usace'),
    ('MFR_00000001', 'port', 'max_vessel_loa_ft', '1000', 'usace'),
    ('MFR_00000001', 'production', 'furnace_type', 'blast_furnace', 'company_report');

-- Sample infrastructure
INSERT INTO facility_infrastructure (
    facility_master_id, infrastructure_type, connection_name, connection_id,
    capacity, operational_status, source_system
) VALUES
    ('MFR_00000001', 'rail', 'Canadian National Railway', 'CN', '12 spurs', 'active', 'rail_scrs'),
    ('MFR_00000001', 'rail', 'CSX Transportation', 'CSX', '12 spurs', 'active', 'rail_scrs'),
    ('MFR_00000001', 'rail', 'Norfolk Southern Railway', 'NS', '12 spurs', 'active', 'rail_scrs'),
    ('MFR_00000001', 'port', 'Port of Indiana-Burns Harbor', 'USBUR', '3 berths, max LOA 1000ft', 'active', 'usace');

-- ============================================================================
-- NOTES ON USAGE
-- ============================================================================

-- Query all facilities by NAICS
-- SELECT * FROM facilities WHERE naics_primary = 331110; -- Steel mills

-- Get facility with all external IDs
-- SELECT * FROM facility_summary WHERE canonical_name LIKE '%Burns Harbor%';

-- Get all facilities with rail access
-- SELECT DISTINCT f.*
-- FROM facilities f
-- JOIN facility_infrastructure i ON f.facility_master_id = i.facility_master_id
-- WHERE i.infrastructure_type = 'rail';

-- Get all EPA FRS IDs for steel mills
-- SELECT f.canonical_name, e.external_id AS epa_frs_id
-- FROM facilities f
-- JOIN facility_external_ids e ON f.facility_master_id = e.facility_master_id
-- WHERE f.naics_primary = 331110 AND e.source_system = 'epa_frs';
