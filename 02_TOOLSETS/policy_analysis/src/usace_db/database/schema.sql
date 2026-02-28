-- ============================================================
-- USACE Vessel Characteristics Database Schema
-- PostgreSQL 15+
-- ============================================================

-- Drop existing objects if rebuilding
DROP VIEW IF EXISTS vessel_analytics_view CASCADE;
DROP TABLE IF EXISTS vessels CASCADE;
DROP TABLE IF EXISTS operators CASCADE;
DROP TABLE IF EXISTS lookup_vtcc CASCADE;
DROP TABLE IF EXISTS lookup_icst CASCADE;
DROP TABLE IF EXISTS lookup_district CASCADE;
DROP TABLE IF EXISTS lookup_series CASCADE;
DROP TABLE IF EXISTS lookup_service CASCADE;
DROP TABLE IF EXISTS lookup_capacity_ref CASCADE;
DROP TABLE IF EXISTS lookup_equipment CASCADE;

-- ============================================================
-- LOOKUP TABLES (Code Translation)
-- ============================================================

-- VTCC Code Lookup (Vessel Type, Construction, Characteristics)
CREATE TABLE lookup_vtcc (
    vtcc_code VARCHAR(4) PRIMARY KEY,
    construction_type VARCHAR(50),
    vessel_type VARCHAR(100),
    characteristic_desc VARCHAR(200),
    is_self_propelled BOOLEAN,
    is_barge BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE lookup_vtcc IS 'Vessel Type, Construction and Characteristics code translations';

-- ICST Code Lookup (International Classification of Ships by Type)
CREATE TABLE lookup_icst (
    icst_code VARCHAR(3) PRIMARY KEY,
    description VARCHAR(200),
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE lookup_icst IS 'International Classification of Ships by Type';

-- Engineering District Lookup
CREATE TABLE lookup_district (
    dist_code INTEGER PRIMARY KEY,
    district_name VARCHAR(100),
    district_abbr VARCHAR(10),
    region VARCHAR(100),
    state VARCHAR(2),
    city VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE lookup_district IS 'Corps of Engineers District codes';

-- Series/Region Lookup
CREATE TABLE lookup_series (
    series_code INTEGER PRIMARY KEY,
    series_name VARCHAR(100),
    description VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE lookup_series IS 'Geographic region series (Great Lakes, Mississippi, Coastal)';

-- Service Type Lookup
CREATE TABLE lookup_service (
    service_code INTEGER PRIMARY KEY,
    service_name VARCHAR(100),
    description VARCHAR(200),
    is_for_hire BOOLEAN,
    regulatory_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE lookup_service IS 'Operator service type classifications';

-- Capacity Reference Lookup
CREATE TABLE lookup_capacity_ref (
    cap_ref_code VARCHAR(1) PRIMARY KEY,
    description VARCHAR(100),
    cargo_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE lookup_capacity_ref IS 'Cargo capacity reference indicators';

-- Equipment Type Lookup
CREATE TABLE lookup_equipment (
    equipment_code VARCHAR(20) PRIMARY KEY,
    equipment_name VARCHAR(100),
    category VARCHAR(50),
    description VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE lookup_equipment IS 'Cargo handling equipment types';

-- ============================================================
-- CORE OPERATIONAL TABLES
-- ============================================================

-- Operator Master Table
CREATE TABLE operators (
    ts_oper INTEGER NOT NULL,
    fleet_year INTEGER NOT NULL,
    operator_name VARCHAR(200) NOT NULL,
    PRIMARY KEY (ts_oper, fleet_year),
    dba VARCHAR(200),
    poc VARCHAR(100),
    address VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(2),
    zip VARCHAR(10),
    area VARCHAR(3),
    phone VARCHAR(20),

    -- Coded fields (no foreign keys to allow loading with incomplete lookup data)
    dist_code INTEGER,
    series_code INTEGER,
    service_code INTEGER,

    -- Business classification
    principal_commodity TEXT,
    point_of_location TEXT,

    -- Vessel count summary fields (from TS_OPER file)
    count_dbc INTEGER DEFAULT 0,
    count_cs INTEGER DEFAULT 0,
    count_gcc INTEGER DEFAULT 0,
    count_sc INTEGER DEFAULT 0,
    count_tan INTEGER DEFAULT 0,
    count_push INTEGER DEFAULT 0,
    count_tug INTEGER DEFAULT 0,
    count_pass INTEGER DEFAULT 0,
    count_osv INTEGER DEFAULT 0,
    count_dcb INTEGER DEFAULT 0,
    count_dob INTEGER DEFAULT 0,
    count_db INTEGER DEFAULT 0,
    count_lsb INTEGER DEFAULT 0,
    count_ody INTEGER DEFAULT 0,
    count_shtb INTEGER DEFAULT 0,
    count_dhtb INTEGER DEFAULT 0,
    count_otb INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE operators IS 'Transportation Series Operator master table - 3,511 operators';
COMMENT ON COLUMN operators.ts_oper IS 'USACE Transportation Series Operator ID (primary key)';
COMMENT ON COLUMN operators.count_dbc IS 'Dry Bulk Carrier count';
COMMENT ON COLUMN operators.count_cs IS 'Containership count';
COMMENT ON COLUMN operators.count_tan IS 'Tanker count';
COMMENT ON COLUMN operators.count_push IS 'Pushboat count';
COMMENT ON COLUMN operators.count_tug IS 'Tugboat count';
COMMENT ON COLUMN operators.count_dcb IS 'Dry Covered Barge count';
COMMENT ON COLUMN operators.count_dob IS 'Dry Open Barge count';
COMMENT ON COLUMN operators.count_db IS 'Deck Barge count';

-- Indexes for operators table
CREATE INDEX idx_operators_name ON operators(operator_name);
CREATE INDEX idx_operators_state ON operators(state);
CREATE INDEX idx_operators_dist ON operators(dist_code);
CREATE INDEX idx_operators_series ON operators(series_code);
CREATE INDEX idx_operators_service ON operators(service_code);

-- Vessel Master Table
CREATE TABLE vessels (
    vessel_id INTEGER NOT NULL,
    fleet_year INTEGER NOT NULL,
    vessel_name VARCHAR(200),
    PRIMARY KEY (vessel_id, fleet_year),
    vs_number VARCHAR(50),
    cg_number VARCHAR(20),

    -- Classification (no foreign keys to allow loading with incomplete lookup data)
    vtcc_code VARCHAR(4),
    icst_code VARCHAR(3),

    -- Physical characteristics
    nrt DECIMAL(10,2),
    horsepower INTEGER,
    reg_length DECIMAL(8,2),
    over_length DECIMAL(8,2),
    reg_breadth DECIMAL(8,2),
    over_breadth DECIMAL(8,2),
    hfp DECIMAL(8,2),

    -- Capacity
    cap_ref_code VARCHAR(1),
    cap_pass INTEGER,
    cap_tons DECIMAL(10,2),

    -- Build information
    year_built INTEGER,
    is_rebuilt BOOLEAN,
    year_rebuilt INTEGER,
    year_vessel INTEGER,

    -- Draft
    load_draft DECIMAL(6,2),
    light_draft DECIMAL(6,2),

    -- Equipment
    equip1 VARCHAR(20),
    equip2 VARCHAR(20),

    -- Location/Registration
    state VARCHAR(2),
    base1 VARCHAR(50),
    base2 VARCHAR(50),
    region_code INTEGER,

    -- Operator relationship
    ts_oper INTEGER,

    -- Source tracking
    source_file VARCHAR(100),

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE vessels IS 'Vessel master table - 45,937 vessels from TS23VS';
COMMENT ON COLUMN vessels.vessel_id IS 'USACE VESSEL ID (primary key)';
COMMENT ON COLUMN vessels.nrt IS 'Net Registered Tonnage (100 cubic feet units)';
COMMENT ON COLUMN vessels.year_vessel IS 'Effective year (rebuilt or original build)';

-- Indexes for vessels table
CREATE INDEX idx_vessels_name ON vessels(vessel_name);
CREATE INDEX idx_vessels_operator ON vessels(ts_oper);
CREATE INDEX idx_vessels_vtcc ON vessels(vtcc_code);
CREATE INDEX idx_vessels_icst ON vessels(icst_code);
CREATE INDEX idx_vessels_state ON vessels(state);
CREATE INDEX idx_vessels_year ON vessels(year_vessel);
CREATE INDEX idx_vessels_cg_number ON vessels(cg_number);
CREATE INDEX idx_vessels_source ON vessels(source_file);

-- ============================================================
-- VIEW - Single Query Dataset
-- All codes pre-translated for instant analytics
-- ============================================================

CREATE VIEW vessel_analytics_view AS
SELECT
    -- Vessel core fields
    v.vessel_id,
    v.vessel_name,
    v.vs_number,
    v.cg_number,

    -- Vessel classification (TRANSLATED)
    v.vtcc_code,
    vtcc.construction_type,
    vtcc.vessel_type AS vtcc_vessel_type,
    vtcc.characteristic_desc,
    vtcc.is_self_propelled,
    vtcc.is_barge,

    v.icst_code,
    icst.description AS icst_description,
    icst.category AS icst_category,

    -- Physical characteristics
    v.nrt,
    v.horsepower,
    v.reg_length,
    v.over_length,
    v.reg_breadth,
    v.over_breadth,
    v.hfp,

    -- Capacity (TRANSLATED)
    v.cap_ref_code,
    cap.description AS capacity_type,
    cap.cargo_type,
    v.cap_pass,
    v.cap_tons,

    -- Build information with calculated age
    v.year_built,
    v.is_rebuilt,
    v.year_rebuilt,
    v.year_vessel,
    (EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER - COALESCE(v.year_vessel, v.year_built)) AS vessel_age,
    CASE
        WHEN COALESCE(v.year_vessel, v.year_built) >= 2010 THEN 'Modern'
        WHEN COALESCE(v.year_vessel, v.year_built) >= 1990 THEN 'Mature'
        ELSE 'Legacy'
    END AS age_category,

    -- Draft
    v.load_draft,
    v.light_draft,

    -- Equipment (TRANSLATED)
    v.equip1,
    eq1.equipment_name AS equip1_name,
    eq1.category AS equip1_category,
    v.equip2,
    eq2.equipment_name AS equip2_name,
    eq2.category AS equip2_category,

    -- Location
    v.state AS vessel_state,
    v.base1,
    v.base2,
    v.region_code,

    -- Series/Region (TRANSLATED)
    op.series_code,
    ser.series_name,
    ser.description AS series_description,

    -- Operator information (TRANSLATED)
    v.ts_oper,
    op.operator_name,
    op.dba,
    op.poc,
    op.address AS operator_address,
    op.city AS operator_city,
    op.state AS operator_state,
    op.zip,
    op.phone,

    -- District (TRANSLATED)
    op.dist_code,
    dist.district_name,
    dist.district_abbr,
    dist.region AS district_region,
    dist.city AS district_city,

    -- Service (TRANSLATED)
    op.service_code,
    svc.service_name,
    svc.is_for_hire,
    svc.regulatory_status,

    op.principal_commodity,
    op.point_of_location,

    -- Operator fleet size (aggregate counts from operator record)
    (COALESCE(op.count_dbc, 0) + COALESCE(op.count_cs, 0) + COALESCE(op.count_gcc, 0) +
     COALESCE(op.count_sc, 0) + COALESCE(op.count_tan, 0) + COALESCE(op.count_push, 0) +
     COALESCE(op.count_tug, 0) + COALESCE(op.count_pass, 0) + COALESCE(op.count_osv, 0) +
     COALESCE(op.count_dcb, 0) + COALESCE(op.count_dob, 0) + COALESCE(op.count_db, 0) +
     COALESCE(op.count_lsb, 0) + COALESCE(op.count_ody, 0) + COALESCE(op.count_shtb, 0) +
     COALESCE(op.count_dhtb, 0) + COALESCE(op.count_otb, 0)) AS operator_total_vessels,

    op.count_tan AS operator_tankers,
    op.count_push AS operator_pushboats,
    op.count_tug AS operator_tugboats,
    op.count_dcb AS operator_covered_barges,
    op.count_dob AS operator_open_barges,
    op.count_db AS operator_deck_barges,

    -- Source tracking
    v.source_file,
    v.fleet_year

FROM vessels v
LEFT JOIN operators op ON v.ts_oper = op.ts_oper
LEFT JOIN lookup_vtcc vtcc ON v.vtcc_code = vtcc.vtcc_code
LEFT JOIN lookup_icst icst ON v.icst_code = icst.icst_code
LEFT JOIN lookup_capacity_ref cap ON v.cap_ref_code = cap.cap_ref_code
LEFT JOIN lookup_equipment eq1 ON v.equip1 = eq1.equipment_code
LEFT JOIN lookup_equipment eq2 ON v.equip2 = eq2.equipment_code
LEFT JOIN lookup_district dist ON op.dist_code = dist.dist_code
LEFT JOIN lookup_series ser ON op.series_code = ser.series_code
LEFT JOIN lookup_service svc ON op.service_code = svc.service_code;

COMMENT ON VIEW vessel_analytics_view IS 'Denormalized view with all codes translated - optimized for dashboard queries';

-- Indexes on materialized view for fast filtering
-- Schema complete
