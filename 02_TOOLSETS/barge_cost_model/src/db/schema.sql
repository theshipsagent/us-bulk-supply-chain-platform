-- Interactive Barge Dashboard Database Schema
-- PostgreSQL with PostGIS for geospatial support

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- ============================================================================
-- WATERWAY NETWORK
-- ============================================================================

CREATE TABLE waterway_links (
    objectid INTEGER PRIMARY KEY,
    id INTEGER,
    length_miles NUMERIC(12, 6),
    dir INTEGER,
    linknum INTEGER NOT NULL,
    anode INTEGER NOT NULL,  -- Start node for routing
    bnode INTEGER NOT NULL,  -- End node for routing
    linkname VARCHAR(255),
    rivername VARCHAR(255),
    amile NUMERIC(12, 6),
    bmile NUMERIC(12, 6),
    length1 NUMERIC(12, 6),
    length_src VARCHAR(50),
    shape_src VARCHAR(50),
    linktype VARCHAR(50),
    waterway VARCHAR(50),
    geo_class VARCHAR(10),
    func_class VARCHAR(10),
    wtwy_type VARCHAR(10),
    chart_id VARCHAR(50),
    num_pairs INTEGER,
    who_mod VARCHAR(50),
    date_mod VARCHAR(50),
    heading VARCHAR(10),
    state VARCHAR(2),
    fips VARCHAR(10),
    fips2 VARCHAR(10),
    non_us VARCHAR(10),
    key_id VARCHAR(100),
    waterway_unique VARCHAR(100),
    min_meas NUMERIC(12, 6),
    max_meas NUMERIC(12, 6),
    shape_length NUMERIC(18, 12),
    geom GEOMETRY(LINESTRING, 4326),

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for graph queries
CREATE INDEX idx_waterway_linknum ON waterway_links(linknum);
CREATE INDEX idx_waterway_anode ON waterway_links(anode);
CREATE INDEX idx_waterway_bnode ON waterway_links(bnode);
CREATE INDEX idx_waterway_nodes ON waterway_links(anode, bnode);
CREATE INDEX idx_waterway_river ON waterway_links(rivername);
CREATE INDEX idx_waterway_state ON waterway_links(state);
CREATE INDEX idx_waterway_geom ON waterway_links USING GIST(geom);

-- ============================================================================
-- LOCKS
-- ============================================================================

CREATE TABLE locks (
    objectid INTEGER PRIMARY KEY,
    id INTEGER,
    ndccode VARCHAR(50),
    region VARCHAR(10),
    rivercd VARCHAR(10),
    lockcd VARCHAR(10),
    chmbcd VARCHAR(10),
    nochmb INTEGER,
    pmsdata VARCHAR(5),
    navstr VARCHAR(100),
    chambn VARCHAR(50),
    chb1 VARCHAR(10),
    str1 VARCHAR(10),
    pmsname VARCHAR(100),
    status VARCHAR(50),
    river VARCHAR(100),
    rivermi NUMERIC(12, 6),
    bank VARCHAR(10),
    lift NUMERIC(12, 6),  -- Lift height in feet
    length NUMERIC(12, 6),  -- Chamber length in feet
    chmbul NUMERIC(12, 6),  -- Chamber usable length
    width NUMERIC(12, 6),  -- Chamber width in feet
    chmbuw NUMERIC(12, 6),  -- Chamber usable width
    audpa NUMERIC(12, 6),  -- Authorized depth point A
    audpb NUMERIC(12, 6),  -- Authorized depth point B
    updpthms NUMERIC(12, 6),  -- Upper pool depth
    lwdpthms NUMERIC(12, 6),  -- Lower pool depth
    yearopen INTEGER,
    gatetype VARCHAR(50),
    gate VARCHAR(50),
    chnlgth NUMERIC(12, 6),  -- Channel length
    chndptha NUMERIC(12, 6),  -- Channel depth A
    chndpthb NUMERIC(12, 6),  -- Channel depth B
    chnwdtha NUMERIC(12, 6),  -- Channel width A
    chnwdthb NUMERIC(12, 6),  -- Channel width B
    wwprjct VARCHAR(100),  -- Waterway project
    mooring VARCHAR(10),
    multi VARCHAR(10),
    division VARCHAR(50),
    district VARCHAR(50),
    state VARCHAR(2),
    maint1 VARCHAR(50),
    oper1 VARCHAR(50),
    owner1 VARCHAR(50),
    town VARCHAR(100),
    county1 VARCHAR(100),
    mooring_r VARCHAR(50),
    x NUMERIC(12, 8),  -- Longitude
    y NUMERIC(12, 8),  -- Latitude
    geom GEOMETRY(POINT, 4326),

    -- Operational data (to be populated later)
    avg_wait_time_minutes INTEGER,
    last_updated TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_locks_river ON locks(river);
CREATE INDEX idx_locks_state ON locks(state);
CREATE INDEX idx_locks_status ON locks(status);
CREATE INDEX idx_locks_geom ON locks USING GIST(geom);

-- ============================================================================
-- DOCKS / NAVIGATION FACILITIES
-- ============================================================================

CREATE TABLE docks (
    objectid INTEGER PRIMARY KEY,
    latitude NUMERIC(12, 8),
    longitude NUMERIC(12, 8),
    loc_dock VARCHAR(50),
    nav_unit_id VARCHAR(50),
    nav_unit_guid VARCHAR(50),
    unlocode VARCHAR(50),
    nav_unit_name VARCHAR(255),
    fac_type VARCHAR(100),
    data_record_status VARCHAR(50),
    location_description TEXT,
    street_address VARCHAR(255),
    city_or_town VARCHAR(100),
    state VARCHAR(2),
    zipcode VARCHAR(20),
    county_name VARCHAR(100),
    county_fips_code VARCHAR(10),
    congress VARCHAR(50),
    congress_fips VARCHAR(10),
    tows_link_num INTEGER,  -- Links to waterway network
    tows_mile NUMERIC(12, 6),
    wtwy VARCHAR(50),
    wtwy_name VARCHAR(255),
    port VARCHAR(50),
    port_name VARCHAR(255),
    psa VARCHAR(50),
    psa_name VARCHAR(255),
    mile NUMERIC(12, 6),
    bank VARCHAR(10),
    operators TEXT,
    owners TEXT,
    purpose TEXT,
    highway_note TEXT,
    railway_note TEXT,
    commodities TEXT,
    construction TEXT,
    mechanical_handling TEXT,
    remarks TEXT,
    vertical_datum VARCHAR(50),
    depth_min NUMERIC(12, 6),  -- Critical for vessel clearance
    depth_max NUMERIC(12, 6),
    berthing_largest NUMERIC(12, 6),
    berthing_total NUMERIC(12, 6),
    deck_height_min NUMERIC(12, 6),
    deck_height_max NUMERIC(12, 6),
    parent_or_child VARCHAR(50),
    service_initiation_date VARCHAR(50),
    x NUMERIC(12, 8),
    y NUMERIC(12, 8),
    geom GEOMETRY(POINT, 4326),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_docks_fac_type ON docks(fac_type);
CREATE INDEX idx_docks_state ON docks(state);
CREATE INDEX idx_docks_port ON docks(port);
CREATE INDEX idx_docks_linknum ON docks(tows_link_num);
CREATE INDEX idx_docks_name ON docks(nav_unit_name);
CREATE INDEX idx_docks_geom ON docks USING GIST(geom);

-- ============================================================================
-- LINK TONNAGES
-- ============================================================================

CREATE TABLE link_tonnages (
    objectid INTEGER PRIMARY KEY,
    linknum INTEGER NOT NULL,  -- Foreign key to waterway_links
    totalup BIGINT DEFAULT 0,
    totaldown BIGINT DEFAULT 0,
    coalup BIGINT DEFAULT 0,
    coaldown BIGINT DEFAULT 0,
    petrolup BIGINT DEFAULT 0,
    petrodown BIGINT DEFAULT 0,
    chemup BIGINT DEFAULT 0,
    chemdown BIGINT DEFAULT 0,
    crmatup BIGINT DEFAULT 0,  -- Crude materials up
    crmatdown BIGINT DEFAULT 0,
    manuup BIGINT DEFAULT 0,  -- Manufactured goods up
    manudown BIGINT DEFAULT 0,
    farmup BIGINT DEFAULT 0,
    farmdown BIGINT DEFAULT 0,
    machup BIGINT DEFAULT 0,
    machdown BIGINT DEFAULT 0,
    wasteup BIGINT DEFAULT 0,
    wastedown BIGINT DEFAULT 0,
    unkwnup BIGINT DEFAULT 0,
    unkwdown BIGINT DEFAULT 0,
    shape_length NUMERIC(18, 12),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tonnages_linknum ON link_tonnages(linknum);

-- ============================================================================
-- VESSELS
-- ============================================================================

CREATE TABLE vessels (
    imo VARCHAR(20) PRIMARY KEY,
    vessel_name VARCHAR(255),
    design VARCHAR(100),
    vessel_type VARCHAR(100),
    dwt INTEGER,  -- Deadweight tonnage
    loa NUMERIC(12, 6),  -- Length overall in meters
    beam NUMERIC(12, 6),  -- Beam width in meters (critical for locks)
    depth_m NUMERIC(12, 6),  -- Draft depth in meters (critical for channels)
    gt INTEGER,  -- Gross tonnage
    nrt INTEGER,  -- Net registered tonnage
    grain INTEGER,
    tpc NUMERIC(12, 6),
    dwt_draft_m NUMERIC(12, 6),
    source_file VARCHAR(255),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_vessels_name ON vessels(vessel_name);
CREATE INDEX idx_vessels_type ON vessels(vessel_type);
CREATE INDEX idx_vessels_beam ON vessels(beam);
CREATE INDEX idx_vessels_draft ON vessels(depth_m);

-- ============================================================================
-- COMPUTED ROUTES (Cache)
-- ============================================================================

CREATE TABLE computed_routes (
    route_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    origin_dock_id INTEGER REFERENCES docks(objectid),
    dest_dock_id INTEGER REFERENCES docks(objectid),
    vessel_imo VARCHAR(20) REFERENCES vessels(imo),
    commodity VARCHAR(100),
    optimization_type VARCHAR(20),  -- 'cost', 'time', 'distance'

    -- Route details
    path_link_ids INTEGER[],  -- Array of waterway link IDs
    path_lock_ids INTEGER[],  -- Array of lock IDs
    total_distance_miles NUMERIC(12, 6),
    transit_time_hours NUMERIC(12, 6),
    total_cost_usd NUMERIC(12, 2),

    -- Cost breakdown
    fuel_cost_usd NUMERIC(12, 2),
    crew_cost_usd NUMERIC(12, 2),
    lock_cost_usd NUMERIC(12, 2),
    delay_cost_usd NUMERIC(12, 2),
    port_cost_usd NUMERIC(12, 2),

    -- Geospatial
    route_geom GEOMETRY(LINESTRING, 4326),

    -- Metadata
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP + INTERVAL '1 hour',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_routes_origin_dest ON computed_routes(origin_dock_id, dest_dock_id);
CREATE INDEX idx_routes_vessel ON computed_routes(vessel_imo);
CREATE INDEX idx_routes_expires ON computed_routes(expires_at);
CREATE INDEX idx_routes_geom ON computed_routes USING GIST(route_geom);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View: Waterway links with tonnage data
CREATE VIEW waterway_links_with_tonnage AS
SELECT
    w.*,
    t.totalup,
    t.totaldown,
    (t.totalup + t.totaldown) as total_tonnage,
    t.coalup, t.coaldown,
    t.petrolup, t.petrodown,
    t.chemup, t.chemdown,
    t.crmatup, t.crmatdown,
    t.manuup, t.manudown,
    t.farmup, t.farmdown
FROM waterway_links w
LEFT JOIN link_tonnages t ON w.linknum = t.linknum;

-- View: Active locks with operational data
CREATE VIEW active_locks AS
SELECT *
FROM locks
WHERE status IS NOT NULL
ORDER BY river, rivermi;

-- View: Cargo docks (facilities that handle cargo)
CREATE VIEW cargo_docks AS
SELECT *
FROM docks
WHERE fac_type IN ('Dock', 'Fleeting_Area', 'Terminal')
ORDER BY state, city_or_town;

-- ============================================================================
-- UTILITY FUNCTIONS
-- ============================================================================

-- Function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update trigger to all tables
CREATE TRIGGER update_waterway_links_updated_at BEFORE UPDATE ON waterway_links
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_locks_updated_at BEFORE UPDATE ON locks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_docks_updated_at BEFORE UPDATE ON docks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_link_tonnages_updated_at BEFORE UPDATE ON link_tonnages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_vessels_updated_at BEFORE UPDATE ON vessels
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE waterway_links IS 'Waterway network segments with routing graph (ANODE->BNODE)';
COMMENT ON TABLE locks IS 'Lock facilities with dimensional constraints for vessel passage';
COMMENT ON TABLE docks IS 'Navigation facilities including docks, terminals, and fleeting areas';
COMMENT ON TABLE link_tonnages IS 'Cargo tonnage by commodity type for each waterway link';
COMMENT ON TABLE vessels IS 'Vessel registry with dimensional specifications';
COMMENT ON TABLE computed_routes IS 'Cached route computations with cost analysis';
