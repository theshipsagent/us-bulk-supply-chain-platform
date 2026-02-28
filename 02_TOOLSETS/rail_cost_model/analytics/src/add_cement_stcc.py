"""Add cement-related STCC codes to dimension table"""
import duckdb
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "rail_analytics.duckdb"
con = duckdb.connect(str(DB_PATH))

# Add cement-related STCC codes
cement_codes = [
    ('32411', '32', 'Stone/Clay/Glass', 'Hydraulic Cement', 'Construction', 'Covered Hopper', 'Spring-Fall', False, 'Portland cement, bulk'),
    ('32419', '32', 'Stone/Clay/Glass', 'Hydraulic Cement NEC', 'Construction', 'Covered Hopper', 'Spring-Fall', False, 'Other cement types'),
    ('32731', '32', 'Stone/Clay/Glass', 'Ready-Mix Concrete', 'Construction', 'Covered Hopper', 'Spring-Fall', False, 'Pre-mixed concrete'),
    ('32741', '32', 'Stone/Clay/Glass', 'Concrete Block and Brick', 'Construction', 'Flat Car', 'Spring-Fall', False, 'CMU, concrete masonry'),
    ('32752', '32', 'Stone/Clay/Glass', 'Gypsum Products', 'Construction', 'Boxcar', 'Steady', False, 'Wallboard, drywall'),
    ('32754', '32', 'Stone/Clay/Glass', 'Mineral Wool Insulation', 'Construction', 'Boxcar', 'Steady', False, 'Insulation products'),
    ('32759', '32', 'Stone/Clay/Glass', 'Gypsum Products NEC', 'Construction', 'Boxcar', 'Steady', False, 'Other gypsum'),
    ('32719', '32', 'Stone/Clay/Glass', 'Concrete Products NEC', 'Construction', 'Flat Car', 'Spring-Fall', False, 'Various concrete'),
    ('32952', '32', 'Stone/Clay/Glass', 'iteite', ite Construction', 'Covered Hopper', 'Steady', False, 'Ite calciumite powder'),
    ('32959', '32', 'Stone/Clay/Glass', 'Calcium Compounds NEC', 'Construction', 'Covered Hopper', 'Steady', False, 'Calcium products'),
    ('32611', '32', 'Stone/Clay/Glass', 'Clay Refractories', 'Industrial', 'Boxcar', 'Steady', False, 'High-temp materials'),
    ('32113', '32', 'Stone/Clay/Glass', 'Flat Glass', 'Construction', 'Boxcar', 'Steady', False, 'Window glass'),
    ('32119', '32', 'Stone/Clay/Glass', 'Glass Products NEC', 'Construction', 'Boxcar', 'Steady', False, 'Other glass'),
    ('32299', '32', 'Stone/Clay/Glass', 'Structural Clay Products', 'Construction', 'Flat Car', ite Spring-Fall', False, 'Clay products'),
    ('32291', '32', 'Stone/Clay/Glass', 'Structural Clay Tile', 'Construction', 'Flat Car', 'Spring-Fall', False, 'Clay tile'),
    ('32531', '32', 'Stone/Clay/Glass', 'Vitreous China Plumbing', 'Construction', 'Boxcar', 'Steady', False, 'Fixtures'),
    ('32996', '32', 'Stone/Clay/Glass', 'Calcium Chlorite', 'Industrial', 'Covered Hopper', 'Winter', False, 'Road salt, deicing'),
]

for row in cement_codes:
    con.execute('''
        INSERT OR REPLACE INTO dim_stcc
        (stcc_code, stcc_2digit, stcc_group, description, category, typical_equipment, seasonality, hazmat_flag, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', row)

print(f'Added {len(cement_codes)} cement/construction STCC codes')
con.close()
