#!/usr/bin/env python3
"""Extract data from ATLAS for market report generation."""

import duckdb
import json
from pathlib import Path

def main():
    con = duckdb.connect("data/atlas.duckdb", read_only=True)
    data = {}

    # 1. US Market Overview
    data["us_capacity"] = con.execute("""
        SELECT ROUND(SUM(capacity_mtpa), 2) as total_capacity,
               COUNT(*) as total_plants,
               COUNT(DISTINCT owner_name) as producers
        FROM gem_cement_plants WHERE country = 'United States'
    """).fetchdf().to_dict(orient="records")[0]

    # 2. Production by company
    data["producers"] = con.execute("""
        SELECT owner_name as company, COUNT(*) as plants,
               ROUND(SUM(capacity_mtpa), 2) as capacity_mtpa,
               ROUND(100.0 * SUM(capacity_mtpa) / (SELECT SUM(capacity_mtpa) FROM gem_cement_plants WHERE country = 'United States'), 1) as market_share
        FROM gem_cement_plants WHERE country = 'United States'
        GROUP BY owner_name ORDER BY capacity_mtpa DESC
    """).fetchdf().to_dict(orient="records")

    # 3. Production by state
    data["capacity_by_state"] = con.execute("""
        SELECT region as state, COUNT(*) as plants,
               ROUND(SUM(capacity_mtpa), 2) as capacity_mtpa
        FROM gem_cement_plants WHERE country = 'United States'
        GROUP BY region ORDER BY capacity_mtpa DESC
    """).fetchdf().to_dict(orient="records")

    # 4. Import totals
    data["import_totals"] = con.execute("""
        SELECT ROUND(SUM(weight_tons)/1000000, 2) as million_tons,
               COUNT(*) as shipments,
               COUNT(DISTINCT origin_country) as countries,
               COUNT(DISTINCT port_of_unlading) as ports,
               COUNT(DISTINCT consignee) as importers,
               MIN(arrival_date) as start_date,
               MAX(arrival_date) as end_date
        FROM trade_imports
    """).fetchdf().to_dict(orient="records")[0]

    # 5. Imports by country
    data["imports_by_country"] = con.execute("""
        SELECT origin_country, COUNT(*) as shipments,
               ROUND(SUM(weight_tons)/1000000, 2) as million_tons,
               ROUND(100.0 * SUM(weight_tons) / (SELECT SUM(weight_tons) FROM trade_imports), 1) as pct_share,
               COUNT(DISTINCT port_of_unlading) as ports_served
        FROM trade_imports GROUP BY origin_country ORDER BY million_tons DESC
    """).fetchdf().to_dict(orient="records")

    # 6. Imports by port
    data["imports_by_port"] = con.execute("""
        SELECT port_of_unlading as port, COUNT(*) as shipments,
               ROUND(SUM(weight_tons)/1000000, 2) as million_tons,
               ROUND(100.0 * SUM(weight_tons) / (SELECT SUM(weight_tons) FROM trade_imports), 1) as pct_share,
               COUNT(DISTINCT origin_country) as source_countries,
               COUNT(DISTINCT consignee) as importers
        FROM trade_imports GROUP BY port_of_unlading ORDER BY million_tons DESC
    """).fetchdf().to_dict(orient="records")

    # 7. Gulf Coast ports detail
    data["gulf_ports"] = con.execute("""
        SELECT port_of_unlading as port, COUNT(*) as shipments,
               ROUND(SUM(weight_tons)/1000000, 2) as million_tons,
               COUNT(DISTINCT origin_country) as countries,
               COUNT(DISTINCT consignee) as importers
        FROM trade_imports
        WHERE port_of_unlading LIKE '%Texas%'
           OR port_of_unlading LIKE '%Louisiana%'
           OR port_of_unlading LIKE '%Alabama%'
           OR port_of_unlading LIKE '%Mississippi%'
        GROUP BY port_of_unlading ORDER BY million_tons DESC
    """).fetchdf().to_dict(orient="records")

    # 8. Florida ports
    data["florida_ports"] = con.execute("""
        SELECT port_of_unlading as port, COUNT(*) as shipments,
               ROUND(SUM(weight_tons)/1000000, 2) as million_tons,
               COUNT(DISTINCT origin_country) as countries,
               COUNT(DISTINCT consignee) as importers
        FROM trade_imports
        WHERE port_of_unlading LIKE '%Florida%'
           OR port_of_unlading LIKE '%Tampa%'
           OR port_of_unlading LIKE '%Miami%'
           OR port_of_unlading LIKE '%Jacksonville%'
           OR port_of_unlading LIKE '%Everglades%'
        GROUP BY port_of_unlading ORDER BY million_tons DESC
    """).fetchdf().to_dict(orient="records")

    # 9. East Coast ports (excl Florida)
    data["east_coast_ports"] = con.execute("""
        SELECT port_of_unlading as port, COUNT(*) as shipments,
               ROUND(SUM(weight_tons)/1000000, 2) as million_tons,
               COUNT(DISTINCT origin_country) as countries,
               COUNT(DISTINCT consignee) as importers
        FROM trade_imports
        WHERE (port_of_unlading LIKE '%New York%'
           OR port_of_unlading LIKE '%Newark%'
           OR port_of_unlading LIKE '%New Jersey%'
           OR port_of_unlading LIKE '%Virginia%'
           OR port_of_unlading LIKE '%Maryland%'
           OR port_of_unlading LIKE '%Delaware%'
           OR port_of_unlading LIKE '%Philadelphia%'
           OR port_of_unlading LIKE '%Rhode Island%'
           OR port_of_unlading LIKE '%Providence%'
           OR port_of_unlading LIKE '%Massachusetts%'
           OR port_of_unlading LIKE '%Boston%'
           OR port_of_unlading LIKE '%South Carolina%'
           OR port_of_unlading LIKE '%Charleston%'
           OR port_of_unlading LIKE '%North Carolina%'
           OR port_of_unlading LIKE '%Savannah%'
           OR port_of_unlading LIKE '%Georgia%')
        GROUP BY port_of_unlading ORDER BY million_tons DESC
    """).fetchdf().to_dict(orient="records")

    # 10. Canada imports detail
    data["canada_imports"] = con.execute("""
        SELECT port_of_unlading as port, COUNT(*) as shipments,
               ROUND(SUM(weight_tons)/1000000, 2) as million_tons
        FROM trade_imports WHERE origin_country = 'Canada'
        GROUP BY port_of_unlading ORDER BY million_tons DESC
    """).fetchdf().to_dict(orient="records")

    # 11. Canada importers
    data["canada_importers"] = con.execute("""
        SELECT consignee as importer, COUNT(*) as shipments,
               ROUND(SUM(weight_tons)/1000000, 2) as million_tons,
               COUNT(DISTINCT port_of_unlading) as ports
        FROM trade_imports WHERE origin_country = 'Canada'
        GROUP BY consignee ORDER BY million_tons DESC
    """).fetchdf().to_dict(orient="records")

    # 12. Top importers overall
    data["top_importers"] = con.execute("""
        SELECT consignee as importer, consignee_parent as parent,
               COUNT(*) as shipments,
               ROUND(SUM(weight_tons)/1000000, 2) as million_tons,
               COUNT(DISTINCT origin_country) as source_countries,
               COUNT(DISTINCT port_of_unlading) as ports_used
        FROM trade_imports GROUP BY consignee, consignee_parent
        ORDER BY million_tons DESC LIMIT 25
    """).fetchdf().to_dict(orient="records")

    # 13. Monthly trends
    data["monthly_trends"] = con.execute("""
        SELECT year, month, COUNT(*) as shipments,
               ROUND(SUM(weight_tons)/1000000, 2) as million_tons
        FROM trade_imports GROUP BY year, month ORDER BY year, month
    """).fetchdf().to_dict(orient="records")

    # 14. Trade flows top 50
    data["trade_flows"] = con.execute("""
        SELECT origin_country, port_of_unlading as port, consignee as importer,
               COUNT(*) as shipments,
               ROUND(SUM(weight_tons)/1000000, 2) as million_tons
        FROM trade_imports GROUP BY origin_country, port_of_unlading, consignee
        ORDER BY million_tons DESC LIMIT 50
    """).fetchdf().to_dict(orient="records")

    # 15. Houston terminal details
    data["houston"] = con.execute("""
        SELECT origin_country, consignee as importer,
               COUNT(*) as shipments,
               ROUND(SUM(weight_tons)/1000000, 2) as million_tons
        FROM trade_imports WHERE port_of_unlading LIKE '%Houston%'
        GROUP BY origin_country, consignee ORDER BY million_tons DESC
    """).fetchdf().to_dict(orient="records")

    # 16. Tampa terminal details
    data["tampa"] = con.execute("""
        SELECT origin_country, consignee as importer,
               COUNT(*) as shipments,
               ROUND(SUM(weight_tons)/1000000, 2) as million_tons
        FROM trade_imports WHERE port_of_unlading LIKE '%Tampa%'
        GROUP BY origin_country, consignee ORDER BY million_tons DESC
    """).fetchdf().to_dict(orient="records")

    # 17. Louisiana/New Orleans details
    data["louisiana"] = con.execute("""
        SELECT port_of_unlading as port, origin_country, consignee as importer,
               COUNT(*) as shipments,
               ROUND(SUM(weight_tons)/1000000, 2) as million_tons
        FROM trade_imports
        WHERE port_of_unlading LIKE '%Louisiana%' OR port_of_unlading LIKE '%Gramercy%' OR port_of_unlading LIKE '%New Orleans%'
        GROUP BY port_of_unlading, origin_country, consignee ORDER BY million_tons DESC
    """).fetchdf().to_dict(orient="records")

    # 18. USGS shipments by state
    data["usgs_shipments"] = con.execute("""
        SELECT state, ROUND(SUM(shipments_short_tons)/1000000, 2) as million_short_tons
        FROM usgs_monthly_shipments
        GROUP BY state ORDER BY million_short_tons DESC LIMIT 30
    """).fetchdf().to_dict(orient="records")

    # 19. Rail served summary
    data["rail_summary"] = con.execute("""
        SELECT facility_type, COUNT(*) as total,
               SUM(CASE WHEN is_rail_served THEN 1 ELSE 0 END) as rail_served
        FROM us_cement_facilities GROUP BY facility_type ORDER BY total DESC
    """).fetchdf().to_dict(orient="records")

    # 20. Plants by state with rail
    data["plants_by_state"] = con.execute("""
        SELECT state,
               COUNT(*) as plants,
               ROUND(SUM(capacity_mtpa), 2) as capacity_mtpa,
               SUM(CASE WHEN is_rail_served THEN 1 ELSE 0 END) as rail_served
        FROM us_cement_facilities WHERE facility_type = 'CEMENT_PLANT'
        GROUP BY state ORDER BY capacity_mtpa DESC
    """).fetchdf().to_dict(orient="records")

    # 21. Savannah/Georgia details
    data["savannah"] = con.execute("""
        SELECT origin_country, consignee as importer,
               COUNT(*) as shipments,
               ROUND(SUM(weight_tons)/1000000, 2) as million_tons
        FROM trade_imports WHERE port_of_unlading LIKE '%Savannah%' OR port_of_unlading LIKE '%Georgia%'
        GROUP BY origin_country, consignee ORDER BY million_tons DESC
    """).fetchdf().to_dict(orient="records")

    # 22. Norfolk/Virginia details
    data["virginia"] = con.execute("""
        SELECT origin_country, consignee as importer,
               COUNT(*) as shipments,
               ROUND(SUM(weight_tons)/1000000, 2) as million_tons
        FROM trade_imports WHERE port_of_unlading LIKE '%Virginia%' OR port_of_unlading LIKE '%Norfolk%'
        GROUP BY origin_country, consignee ORDER BY million_tons DESC
    """).fetchdf().to_dict(orient="records")

    # 23. NY/NJ details
    data["nynj"] = con.execute("""
        SELECT origin_country, consignee as importer,
               COUNT(*) as shipments,
               ROUND(SUM(weight_tons)/1000000, 2) as million_tons
        FROM trade_imports
        WHERE port_of_unlading LIKE '%New York%' OR port_of_unlading LIKE '%Newark%' OR port_of_unlading LIKE '%New Jersey%'
        GROUP BY origin_country, consignee ORDER BY million_tons DESC
    """).fetchdf().to_dict(orient="records")

    # 24. Providence/Rhode Island
    data["providence"] = con.execute("""
        SELECT origin_country, consignee as importer,
               COUNT(*) as shipments,
               ROUND(SUM(weight_tons)/1000000, 2) as million_tons
        FROM trade_imports WHERE port_of_unlading LIKE '%Rhode Island%' OR port_of_unlading LIKE '%Providence%'
        GROUP BY origin_country, consignee ORDER BY million_tons DESC
    """).fetchdf().to_dict(orient="records")

    # 25. Philadelphia
    data["philadelphia"] = con.execute("""
        SELECT origin_country, consignee as importer,
               COUNT(*) as shipments,
               ROUND(SUM(weight_tons)/1000000, 2) as million_tons
        FROM trade_imports WHERE port_of_unlading LIKE '%Philadelphia%' OR port_of_unlading LIKE '%Pennsylvania%'
        GROUP BY origin_country, consignee ORDER BY million_tons DESC
    """).fetchdf().to_dict(orient="records")

    # 26. Annual import trends
    data["annual_imports"] = con.execute("""
        SELECT year, COUNT(*) as shipments,
               ROUND(SUM(weight_tons)/1000000, 2) as million_tons,
               COUNT(DISTINCT origin_country) as countries,
               COUNT(DISTINCT consignee) as importers
        FROM trade_imports GROUP BY year ORDER BY year
    """).fetchdf().to_dict(orient="records")

    # 27. Turkey flows detail (largest source)
    data["turkey_flows"] = con.execute("""
        SELECT port_of_unlading as port, consignee as importer,
               COUNT(*) as shipments,
               ROUND(SUM(weight_tons)/1000000, 2) as million_tons
        FROM trade_imports WHERE origin_country = 'Turkey'
        GROUP BY port_of_unlading, consignee ORDER BY million_tons DESC
    """).fetchdf().to_dict(orient="records")

    # 28. Gulf Coast states production
    data["gulf_production"] = con.execute("""
        SELECT region as state, owner_name as company, plant_name,
               ROUND(capacity_mtpa, 2) as capacity_mtpa
        FROM gem_cement_plants
        WHERE country = 'United States'
          AND region IN ('Texas', 'Louisiana', 'Alabama', 'Mississippi', 'Florida')
        ORDER BY capacity_mtpa DESC
    """).fetchdf().to_dict(orient="records")

    # 29. East Coast states production
    data["east_coast_production"] = con.execute("""
        SELECT region as state, owner_name as company, plant_name,
               ROUND(capacity_mtpa, 2) as capacity_mtpa
        FROM gem_cement_plants
        WHERE country = 'United States'
          AND region IN ('New York', 'New Jersey', 'Pennsylvania', 'Maryland', 'Virginia',
                         'West Virginia', 'North Carolina', 'South Carolina', 'Georgia')
        ORDER BY capacity_mtpa DESC
    """).fetchdf().to_dict(orient="records")

    # 30. Competitor imports analysis
    data["competitor_imports"] = con.execute("""
        SELECT consignee as importer,
               ROUND(SUM(weight_tons)/1000000, 2) as total_million_tons,
               ROUND(SUM(CASE WHEN port_of_unlading LIKE '%Texas%' OR port_of_unlading LIKE '%Louisiana%' THEN weight_tons ELSE 0 END)/1000000, 2) as gulf_mt,
               ROUND(SUM(CASE WHEN port_of_unlading LIKE '%Florida%' OR port_of_unlading LIKE '%Tampa%' OR port_of_unlading LIKE '%Everglades%' THEN weight_tons ELSE 0 END)/1000000, 2) as florida_mt,
               ROUND(SUM(CASE WHEN port_of_unlading LIKE '%Georgia%' OR port_of_unlading LIKE '%Savannah%' THEN weight_tons ELSE 0 END)/1000000, 2) as georgia_mt,
               ROUND(SUM(CASE WHEN port_of_unlading LIKE '%New York%' OR port_of_unlading LIKE '%Newark%' THEN weight_tons ELSE 0 END)/1000000, 2) as nynj_mt
        FROM trade_imports
        GROUP BY consignee ORDER BY total_million_tons DESC LIMIT 20
    """).fetchdf().to_dict(orient="records")

    con.close()

    # Save to JSON
    output_path = Path("output/report_data.json")
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2, default=str)

    print(f"Data extracted and saved to {output_path}")
    print(f"Total keys: {len(data.keys())}")
    for key in data.keys():
        if isinstance(data[key], list):
            print(f"  {key}: {len(data[key])} records")
        else:
            print(f"  {key}: dict")

if __name__ == "__main__":
    main()
