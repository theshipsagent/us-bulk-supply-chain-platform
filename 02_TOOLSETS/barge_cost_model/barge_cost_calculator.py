"""
Unified Barge Cost Calculator

Select origin (river + mile marker) and destination (river + mile marker).
Calculates:
  - Route through river network (via junctions if different rivers)
  - Locks encountered and delay time
  - Transit time at standard barge/tug speeds
  - Forecasted barge rate (USDA tariff method)
  - Cost per ton and cost per ton-mile
  - Rail comparison
"""

import pickle
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import networkx as nx

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Lock:
    name: str
    river: str
    mile: float
    length_ft: float
    width_ft: float
    lift_ft: float
    lat: float
    lon: float
    avg_delay_hours: float = 2.0  # default; 600-ft locks get more

    @property
    def is_600ft(self) -> bool:
        return self.length_ft <= 600

    def estimated_delay(self, tow_length_ft: float = 1200) -> float:
        """Estimate delay based on chamber size vs tow size."""
        if tow_length_ft > self.length_ft:
            # Double lockage required - much longer
            return 3.5  # hours for double lockage
        else:
            return 1.5  # single lockage


@dataclass
class RiverJunction:
    name: str
    river_a: str
    river_b: str
    mile_on_a: float
    mile_on_b: float
    lat: float
    lon: float


@dataclass
class WaterwayLink:
    linknum: int
    anode: int
    bnode: int
    rivername: str
    amile: float
    bmile: float
    length: float
    state: str


@dataclass
class RouteResult:
    origin_river: str
    origin_mile: float
    dest_river: str
    dest_mile: float
    total_distance_miles: float
    segments: List[dict]  # [{river, from_mile, to_mile, distance, locks:[]}]
    locks_encountered: List[Lock]
    transit_time_hours: float
    lock_delay_hours: float
    total_time_hours: float
    total_time_days: float
    # Cost fields
    usda_segments_used: List[int]
    forecasted_rate_per_ton: float
    rate_plus_markup: float
    cost_per_ton_mile: float
    total_cost_per_ton: float
    # Rail comparison
    rail_cost_per_ton_mile: float
    rail_cost_per_ton: float
    barge_savings_per_ton: float
    barge_savings_pct: float
    # Operational costs
    fuel_cost: float
    crew_cost: float
    lock_fees: float
    total_operational_cost: float
    cost_per_ton_operational: float


# ---------------------------------------------------------------------------
# USDA segment mapping
# ---------------------------------------------------------------------------
# Segments correspond to the 7 zones in the USDA Grain Transportation Report
#
# UPPER Mississippi mile system: Mile 0 = Cairo/Ohio junction, miles increase
# going UPSTREAM (north) toward Minneapolis (Mile ~858).
# Locks 1-27 are on the Upper Mississippi between Mile 185 and Mile 854.
#
# LOWER Mississippi mile system: Mile 0 = Head of Passes/Gulf, miles increase
# going UPSTREAM toward Cairo (~Mile 954). NO locks on Lower Mississippi.
#
# Our data uses Upper Mississippi miles for "MISSISSIPPI RIVER" (0-858).

USDA_SEGMENT_DEFINITIONS = {
    1: {
        "name": "Upper Mississippi (Twin Cities to Lock 13)",
        "river": "MISSISSIPPI RIVER",
        "mile_start": 522,  # Lock 13
        "mile_end": 858,    # Minneapolis
        "description": "Twin Cities, MN to Mid-Mississippi"
    },
    2: {
        "name": "Mid-Mississippi (Lock 13 to St. Louis)",
        "river": "MISSISSIPPI RIVER",
        "mile_start": 185,  # Mel Price / Chain of Rocks
        "mile_end": 522,    # Lock 13
        "description": "Mid-Mississippi to St. Louis, MO"
    },
    3: {
        "name": "Illinois River",
        "river": "ILLINOIS RIVER",
        "mile_start": 0,
        "mile_end": 327,
        "description": "Illinois Waterway"
    },
    4: {
        "name": "Ohio River",
        "river": "OHIO RIVER",
        "mile_start": 0,    # Pittsburgh
        "mile_end": 981,    # Cairo
        "description": "Ohio River (Pittsburgh to Cairo)"
    },
    5: {
        "name": "Cairo to Memphis",
        "river": "LOWER MISSISSIPPI",
        "mile_start": 0,    # Cairo (Upper Miss Mile 0)
        "mile_end": 220,    # ~220 miles Cairo to Memphis
        "description": "Cairo, IL to Memphis, TN"
    },
    6: {
        "name": "Memphis to Greenville",
        "river": "LOWER MISSISSIPPI",
        "mile_start": 220,
        "mile_end": 420,    # ~200 miles Memphis to Greenville
        "description": "Memphis, TN to Greenville, MS"
    },
    7: {
        "name": "Greenville to New Orleans",
        "river": "LOWER MISSISSIPPI",
        "mile_start": 420,
        "mile_end": 850,    # ~430 miles Greenville to New Orleans
        "description": "Greenville, MS to New Orleans/Gulf"
    },
}

# Key river junctions (manual from data)
# Upper Mississippi Mile 0 = Cairo (Ohio River junction)
# Miles increase going upstream (north) toward Minneapolis
KNOWN_JUNCTIONS = {
    ("OHIO RIVER", "MISSISSIPPI RIVER"): {
        "name": "Ohio-Mississippi Confluence (Cairo, IL)",
        "ohio_mile": 981,
        "mississippi_mile": 0,    # Upper Miss Mile 0 = Cairo
    },
    ("ILLINOIS RIVER", "MISSISSIPPI RIVER"): {
        "name": "Illinois-Mississippi Confluence (Grafton, IL)",
        "illinois_mile": 0,
        "mississippi_mile": 218,  # Upper Miss Mile 218
    },
    ("MISSOURI RIVER", "MISSISSIPPI RIVER"): {
        "name": "Missouri-Mississippi Confluence (Hartford, IL)",
        "missouri_mile": 0,
        "mississippi_mile": 195,  # Upper Miss Mile 195
    },
    ("TENNESSEE RIVER", "OHIO RIVER"): {
        "name": "Tennessee-Ohio Confluence (Paducah, KY)",
        "tennessee_mile": 0,
        "ohio_mile": 918,
    },
    ("CUMBERLAND RIVER", "OHIO RIVER"): {
        "name": "Cumberland-Ohio Confluence",
        "cumberland_mile": 0,
        "ohio_mile": 918,
    },
    ("ARKANSAS RIVER", "MISSISSIPPI RIVER"): {
        "name": "Arkansas-Mississippi Confluence",
        "arkansas_mile": 0,
        "mississippi_mile": 0,    # Near Cairo on the Lower Miss
    },
    ("MONONGAHELA RIVER", "OHIO RIVER"): {
        "name": "Monongahela-Ohio Confluence (Pittsburgh)",
        "monongahela_mile": 0,
        "ohio_mile": 0,
    },
    ("ALLEGHENY RIVER", "OHIO RIVER"): {
        "name": "Allegheny-Ohio Confluence (Pittsburgh)",
        "allegheny_mile": 0,
        "ohio_mile": 0,
    },
}


# ---------------------------------------------------------------------------
# Main calculator class
# ---------------------------------------------------------------------------

class BargeCostCalculator:
    """
    Unified barge costing calculator.

    Usage:
        calc = BargeCostCalculator()
        calc.load_data()
        result = calc.calculate_route_cost(
            origin_river="ILLINOIS RIVER", origin_mile=231,
            dest_river="MISSISSIPPI RIVER", dest_mile=100
        )
    """

    # Operational constants
    BARGE_SPEED_MPH_DOWNSTREAM = 8.0   # loaded, downstream
    BARGE_SPEED_MPH_UPSTREAM = 5.0     # loaded, upstream
    BARGE_SPEED_MPH_AVG = 6.0          # average
    TOW_LENGTH_FT = 1200               # standard 15-barge tow
    CARGO_TONS_PER_BARGE = 1500        # ~1500 tons per jumbo hopper barge
    BARGES_PER_TOW = 15                # standard tow configuration
    TOTAL_TOW_TONS = 1500 * 15         # 22,500 tons

    # Operational cost constants
    FUEL_GALLONS_PER_DAY = 3000        # towboat fuel consumption
    FUEL_PRICE_PER_GALLON = 3.50       # USD
    CREW_SIZE = 12
    CREW_COST_PER_DAY = 1200           # per crew member
    LOCK_FEE_PER_PASSAGE = 50          # USD average

    # Rate constants
    USDA_MARKUP_PER_TON = 2.00         # user's $2 markup
    RAIL_COST_PER_TON_MILE = 0.04      # default rail comparison rate

    def __init__(self):
        self.locks: List[Lock] = []
        self.links: pd.DataFrame = None
        self.graph: Optional[nx.Graph] = None
        self.rate_data: Optional[pd.DataFrame] = None
        self.var_model = None
        self.rivers_available: List[str] = []
        self._loaded = False

    def load_data(self) -> dict:
        """Load all required data files. Returns status dict."""
        status = {}

        # 1. Load locks
        try:
            locks_path = PROJECT_ROOT / "data" / "04_bts_locks" / "Locks_-3795028687405442582.csv"
            locks_df = pd.read_csv(locks_path, encoding='latin1')
            self.locks = []
            for _, row in locks_df.iterrows():
                if pd.notna(row.get('RIVER')) and pd.notna(row.get('RIVERMI')):
                    self.locks.append(Lock(
                        name=str(row.get('PMSNAME', 'Unknown')),
                        river=str(row['RIVER']).upper().strip(),
                        mile=float(row['RIVERMI']),
                        length_ft=float(row.get('LENGTH', 600) or 600),
                        width_ft=float(row.get('WIDTH', 110) or 110),
                        lift_ft=float(row.get('LIFT', 0) or 0),
                        lat=float(row.get('y', 0) or 0),
                        lon=float(row.get('x', 0) or 0),
                    ))
            status['locks'] = f"{len(self.locks)} locks loaded"
        except Exception as e:
            status['locks'] = f"FAILED: {e}"

        # 2. Load waterway links
        try:
            links_path = PROJECT_ROOT / "data" / "09_bts_waterway_networks" / "Waterway_Networks_7107995240912772581.csv"
            self.links = pd.read_csv(links_path, encoding='latin1')
            self.links.columns = [c.strip().lstrip('\ufeff') for c in self.links.columns]
            self.rivers_available = sorted(
                self.links['RIVERNAME'].dropna().unique().tolist()
            )
            status['links'] = f"{len(self.links)} waterway links loaded"
        except Exception as e:
            status['links'] = f"FAILED: {e}"

        # 3. Load (or build) graph
        try:
            graph_path = PROJECT_ROOT / "models" / "waterway_graph.pkl"
            if graph_path.exists():
                with open(graph_path, 'rb') as f:
                    self.graph = pickle.load(f)
                status['graph'] = f"{len(self.graph.nodes())} nodes, {len(self.graph.edges())} edges"
            else:
                # Build from links
                self.graph = self._build_graph()
                status['graph'] = f"Built: {len(self.graph.nodes())} nodes"
        except Exception as e:
            status['graph'] = f"FAILED: {e}"

        # 4. Load rate data
        try:
            rate_path = PROJECT_ROOT / "forecasting" / "data" / "processed" / "barge_rates_processed_full.csv"
            self.rate_data = pd.read_csv(rate_path)
            self.rate_data['date'] = pd.to_datetime(self.rate_data['date'])
            status['rates'] = f"{len(self.rate_data)} weeks of rate data"
        except Exception as e:
            status['rates'] = f"FAILED: {e}"

        # 5. Try to load VAR model
        try:
            model_path = PROJECT_ROOT / "forecasting" / "models" / "var" / "var_model_lag3.pkl"
            if model_path.exists():
                with open(model_path, 'rb') as f:
                    self.var_model = pickle.load(f)
                status['var_model'] = "Loaded"
            else:
                status['var_model'] = "Not found (will use recent actuals)"
        except Exception as e:
            status['var_model'] = f"FAILED: {e}"

        self._loaded = True
        return status

    def _build_graph(self) -> nx.Graph:
        """Build NetworkX graph from links data."""
        G = nx.Graph()
        for _, row in self.links.iterrows():
            anode = row.get('ANODE')
            bnode = row.get('BNODE')
            length = row.get('LENGTH', 0) or 0
            if pd.notna(anode) and pd.notna(bnode):
                G.add_edge(
                    int(anode), int(bnode),
                    length=float(length),
                    linknum=row.get('LINKNUM'),
                    rivername=row.get('RIVERNAME'),
                    amile=row.get('AMILE'),
                    bmile=row.get('BMILE'),
                )
        return G

    # ------------------------------------------------------------------
    # River / mile marker → node mapping
    # ------------------------------------------------------------------

    def get_rivers(self) -> List[str]:
        """Get list of available rivers."""
        # Return major navigable rivers first
        major = [
            "MISSISSIPPI RIVER",
            "OHIO RIVER",
            "ILLINOIS RIVER",
            "MISSOURI RIVER",
            "TENNESSEE RIVER",
            "ARKANSAS RIVER",
            "CUMBERLAND RIVER",
            "MONONGAHELA RIVER",
            "ALLEGHENY RIVER",
        ]
        available = [r for r in major if r in self.rivers_available]
        others = [r for r in self.rivers_available if r not in major]
        return available + others

    def get_mile_range(self, river: str) -> Tuple[float, float]:
        """Get (min_mile, max_mile) for a river."""
        river_links = self.links[self.links['RIVERNAME'] == river]
        if river_links.empty:
            return (0, 0)
        all_miles = pd.concat([river_links['AMILE'], river_links['BMILE']]).dropna()
        return (float(all_miles.min()), float(all_miles.max()))

    def get_locks_on_river(self, river: str) -> List[Lock]:
        """Get all locks on a river, sorted by mile."""
        river_upper = river.upper().strip()
        # Match on river name (handles slight variations)
        river_locks = []
        for lock in self.locks:
            lock_river = lock.river.upper().strip()
            # Handle partial matches (e.g., "MISSISSIPPI" in "MISSISSIPPI RIVER")
            if river_upper in lock_river or lock_river in river_upper:
                river_locks.append(lock)
        return sorted(river_locks, key=lambda l: l.mile)

    def _find_nearest_node(self, river: str, mile: float) -> Optional[int]:
        """Find the graph node nearest to a river mile marker."""
        river_links = self.links[self.links['RIVERNAME'] == river].copy()
        if river_links.empty:
            return None

        # Find link where mile falls between AMILE and BMILE
        for _, row in river_links.iterrows():
            amile = row.get('AMILE', 0) or 0
            bmile = row.get('BMILE', 0) or 0
            lo, hi = min(amile, bmile), max(amile, bmile)
            if lo <= mile <= hi:
                # Return the closer node
                if abs(mile - amile) <= abs(mile - bmile):
                    return int(row['ANODE'])
                else:
                    return int(row['BNODE'])

        # If no exact match, find closest link
        river_links['dist_a'] = abs(river_links['AMILE'] - mile)
        river_links['dist_b'] = abs(river_links['BMILE'] - mile)
        river_links['min_dist'] = river_links[['dist_a', 'dist_b']].min(axis=1)
        closest = river_links.loc[river_links['min_dist'].idxmin()]
        if closest['dist_a'] <= closest['dist_b']:
            return int(closest['ANODE'])
        else:
            return int(closest['BNODE'])

    # ------------------------------------------------------------------
    # Lock detection along route
    # ------------------------------------------------------------------

    def _find_locks_between(self, river: str, mile_a: float, mile_b: float) -> List[Lock]:
        """Find all locks on a river between two mile markers."""
        lo, hi = min(mile_a, mile_b), max(mile_a, mile_b)
        river_locks = self.get_locks_on_river(river)
        return [l for l in river_locks if lo <= l.mile <= hi]

    # ------------------------------------------------------------------
    # Route calculation
    # ------------------------------------------------------------------

    def _calculate_direct_route(
        self, river: str, origin_mile: float, dest_mile: float
    ) -> dict:
        """Calculate route on a single river (no junction needed)."""
        distance = abs(dest_mile - origin_mile)
        locks = self._find_locks_between(river, origin_mile, dest_mile)
        going_downstream = dest_mile < origin_mile  # lower mile = downstream

        return {
            "river": river,
            "from_mile": origin_mile,
            "to_mile": dest_mile,
            "distance": distance,
            "downstream": going_downstream,
            "locks": locks,
        }

    def _find_junction(self, river_a: str, river_b: str, _depth: int = 0) -> Optional[dict]:
        """Find junction between two rivers."""
        # Check both orderings in KNOWN_JUNCTIONS
        for key in [(river_a, river_b), (river_b, river_a)]:
            if key in KNOWN_JUNCTIONS:
                jct = KNOWN_JUNCTIONS[key]
                r1, r2 = key
                mile_key_1 = r1.split()[0].lower() + "_mile"
                mile_key_2 = r2.split()[0].lower() + "_mile"
                return {
                    "name": jct["name"],
                    "rivers": key,
                    "miles": {
                        r1: jct.get(mile_key_1, 0),
                        r2: jct.get(mile_key_2, 0),
                    }
                }

        # Prevent infinite recursion
        if _depth > 0:
            return None

        # Try to find indirect junction (e.g., Illinois → Mississippi → ...)
        miss = "MISSISSIPPI RIVER"
        ohio = "OHIO RIVER"

        jct_a_miss = self._find_junction(river_a, miss, _depth=1)
        jct_b_miss = self._find_junction(river_b, miss, _depth=1)

        # Both connect to Mississippi
        if jct_a_miss and jct_b_miss:
            return {
                "name": f"Via Mississippi River",
                "type": "indirect",
                "junction_a": jct_a_miss,
                "junction_b": jct_b_miss,
                "via_river": miss,
            }

        jct_a_ohio = self._find_junction(river_a, ohio, _depth=1)
        jct_b_ohio = self._find_junction(river_b, ohio, _depth=1)

        # Both connect to Ohio
        if jct_a_ohio and jct_b_ohio:
            return {
                "name": f"Via Ohio River",
                "type": "indirect",
                "junction_a": jct_a_ohio,
                "junction_b": jct_b_ohio,
                "via_river": ohio,
            }

        # One connects to Ohio, other to Mississippi (route via both)
        if jct_a_ohio and jct_b_miss:
            return {
                "name": f"Via Ohio & Mississippi Rivers",
                "type": "indirect_2",
                "junction_a": jct_a_ohio,
                "junction_b": jct_b_miss,
                "via_rivers": [ohio, miss],
            }
        if jct_a_miss and jct_b_ohio:
            return {
                "name": f"Via Mississippi & Ohio Rivers",
                "type": "indirect_2",
                "junction_a": jct_a_miss,
                "junction_b": jct_b_ohio,
                "via_rivers": [miss, ohio],
            }

        return None

    def calculate_route_cost(
        self,
        origin_river: str,
        origin_mile: float,
        dest_river: str,
        dest_mile: float,
        cargo_tons: int = None,
        tow_config: str = "15-barge",
        speed_mph: float = None,
        rail_rate: float = None,
        markup_per_ton: float = None,
    ) -> RouteResult:
        """
        Calculate complete route cost between two points.

        Args:
            origin_river: River name (e.g., "ILLINOIS RIVER")
            origin_mile: Mile marker on origin river
            dest_river: River name (e.g., "MISSISSIPPI RIVER")
            dest_mile: Mile marker on destination river
            cargo_tons: Total cargo tonnage (default: 22,500 for 15-barge tow)
            tow_config: Tow configuration ("15-barge", "6-barge", etc.)
            speed_mph: Override average speed
            rail_rate: Rail comparison rate per ton-mile
            markup_per_ton: USDA tariff markup per ton
        """
        if not self._loaded:
            raise RuntimeError("Call load_data() first")

        # Defaults
        if cargo_tons is None:
            cargo_tons = self.TOTAL_TOW_TONS
        if speed_mph is None:
            speed_mph = self.BARGE_SPEED_MPH_AVG
        if rail_rate is None:
            rail_rate = self.RAIL_COST_PER_TON_MILE
        if markup_per_ton is None:
            markup_per_ton = self.USDA_MARKUP_PER_TON

        tow_length = 1200 if "15" in tow_config else 600

        # ---- Build route segments ----
        segments = []
        all_locks = []

        if origin_river == dest_river:
            # Same river - direct route
            seg = self._calculate_direct_route(origin_river, origin_mile, dest_mile)
            segments.append(seg)
            all_locks.extend(seg['locks'])
        else:
            # Different rivers - find junction(s)
            junction = self._find_junction(origin_river, dest_river)
            if not junction:
                raise ValueError(
                    f"No known route between {origin_river} and {dest_river}. "
                    f"Supported rivers: Mississippi, Ohio, Illinois, Missouri, "
                    f"Tennessee, Arkansas, Cumberland, Monongahela, Allegheny."
                )

            if junction.get("type") == "indirect":
                # Route: origin_river → Mississippi → dest_river
                via = junction["via_river"]
                jct_a = junction["junction_a"]
                jct_b = junction["junction_b"]

                # Segment 1: origin to junction with Mississippi
                mile_at_jct_a = jct_a["miles"][origin_river]
                seg1 = self._calculate_direct_route(origin_river, origin_mile, mile_at_jct_a)
                segments.append(seg1)
                all_locks.extend(seg1['locks'])

                # Segment 2: on Mississippi between the two junctions
                miss_mile_a = jct_a["miles"][via]
                miss_mile_b = jct_b["miles"][via]
                seg2 = self._calculate_direct_route(via, miss_mile_a, miss_mile_b)
                segments.append(seg2)
                all_locks.extend(seg2['locks'])

                # Segment 3: junction with dest river to destination
                mile_at_jct_b = jct_b["miles"][dest_river]
                seg3 = self._calculate_direct_route(dest_river, mile_at_jct_b, dest_mile)
                segments.append(seg3)
                all_locks.extend(seg3['locks'])

            elif junction.get("type") == "indirect_2":
                # Route through two intermediate rivers
                jct_a = junction["junction_a"]
                jct_b = junction["junction_b"]
                via_rivers = junction["via_rivers"]

                # Segment 1: origin to junction A
                mile_at_jct_a = jct_a["miles"][origin_river]
                seg1 = self._calculate_direct_route(origin_river, origin_mile, mile_at_jct_a)
                segments.append(seg1)
                all_locks.extend(seg1['locks'])

                # Segment 2: on first via river (Ohio) to Ohio-Miss junction
                via_r1 = via_rivers[0]
                ohio_mile_start = jct_a["miles"][via_r1]
                ohio_miss_jct = KNOWN_JUNCTIONS.get(
                    ("OHIO RIVER", "MISSISSIPPI RIVER"), {}
                )
                ohio_mile_end = ohio_miss_jct.get("ohio_mile", 981)
                seg2 = self._calculate_direct_route(via_r1, ohio_mile_start, ohio_mile_end)
                segments.append(seg2)
                all_locks.extend(seg2['locks'])

                # Segment 3: on Mississippi
                via_r2 = via_rivers[1]
                miss_mile_start = ohio_miss_jct.get("mississippi_mile", 953)
                miss_mile_end = jct_b["miles"][via_r2]
                seg3 = self._calculate_direct_route(via_r2, miss_mile_start, miss_mile_end)
                segments.append(seg3)
                all_locks.extend(seg3['locks'])

                # Segment 4: dest river
                mile_at_jct_b = jct_b["miles"][dest_river]
                seg4 = self._calculate_direct_route(dest_river, mile_at_jct_b, dest_mile)
                segments.append(seg4)
                all_locks.extend(seg4['locks'])

            else:
                # Direct junction between two rivers
                origin_jct_mile = junction["miles"].get(origin_river, 0)
                dest_jct_mile = junction["miles"].get(dest_river, 0)

                # Segment 1: origin to junction
                seg1 = self._calculate_direct_route(origin_river, origin_mile, origin_jct_mile)
                segments.append(seg1)
                all_locks.extend(seg1['locks'])

                # Segment 2: junction to destination
                seg2 = self._calculate_direct_route(dest_river, dest_jct_mile, dest_mile)
                segments.append(seg2)
                all_locks.extend(seg2['locks'])

        # ---- Calculate totals ----
        total_distance = sum(s['distance'] for s in segments)

        # Lock delays
        total_lock_delay = sum(
            lock.estimated_delay(tow_length) for lock in all_locks
        )

        # Transit time
        transit_hours = total_distance / speed_mph if speed_mph > 0 else 0
        total_hours = transit_hours + total_lock_delay
        total_days = total_hours / 24

        # ---- USDA rate forecasting ----
        usda_segments = self._map_to_usda_segments(segments)
        forecasted_rate = self._get_forecasted_rate(usda_segments)
        rate_with_markup = forecasted_rate + markup_per_ton
        cost_per_ton_mile = rate_with_markup / total_distance if total_distance > 0 else 0
        total_cost_per_ton = rate_with_markup  # This IS the per-ton cost

        # ---- Rail comparison ----
        rail_cost_per_ton = rail_rate * total_distance
        barge_savings = rail_cost_per_ton - total_cost_per_ton
        barge_savings_pct = (barge_savings / rail_cost_per_ton * 100) if rail_cost_per_ton > 0 else 0

        # ---- Operational costs (for the full tow) ----
        fuel_cost = (transit_hours / 24) * self.FUEL_GALLONS_PER_DAY * self.FUEL_PRICE_PER_GALLON
        crew_cost = self.CREW_SIZE * self.CREW_COST_PER_DAY * total_days
        lock_fees = len(all_locks) * self.LOCK_FEE_PER_PASSAGE
        total_op_cost = fuel_cost + crew_cost + lock_fees
        cost_per_ton_op = total_op_cost / cargo_tons if cargo_tons > 0 else 0

        # ---- Build segment summaries ----
        segment_summaries = []
        for seg in segments:
            segment_summaries.append({
                "river": seg["river"],
                "from_mile": seg["from_mile"],
                "to_mile": seg["to_mile"],
                "distance": seg["distance"],
                "direction": "downstream" if seg.get("downstream") else "upstream",
                "locks": [{"name": l.name, "mile": l.mile, "length_ft": l.length_ft,
                           "delay_hrs": l.estimated_delay(tow_length)} for l in seg["locks"]],
                "num_locks": len(seg["locks"]),
            })

        return RouteResult(
            origin_river=origin_river,
            origin_mile=origin_mile,
            dest_river=dest_river,
            dest_mile=dest_mile,
            total_distance_miles=total_distance,
            segments=segment_summaries,
            locks_encountered=all_locks,
            transit_time_hours=transit_hours,
            lock_delay_hours=total_lock_delay,
            total_time_hours=total_hours,
            total_time_days=total_days,
            usda_segments_used=usda_segments,
            forecasted_rate_per_ton=forecasted_rate,
            rate_plus_markup=rate_with_markup,
            cost_per_ton_mile=cost_per_ton_mile,
            total_cost_per_ton=total_cost_per_ton,
            rail_cost_per_ton_mile=rail_rate,
            rail_cost_per_ton=rail_cost_per_ton,
            barge_savings_per_ton=barge_savings,
            barge_savings_pct=barge_savings_pct,
            fuel_cost=fuel_cost,
            crew_cost=crew_cost,
            lock_fees=lock_fees,
            total_operational_cost=total_op_cost,
            cost_per_ton_operational=cost_per_ton_op,
        )

    # ------------------------------------------------------------------
    # USDA segment mapping and rate forecasting
    # ------------------------------------------------------------------

    def _map_to_usda_segments(self, segments: List[dict]) -> List[int]:
        """Map route segments to USDA rate zone segment numbers."""
        used_segments = set()

        for seg in segments:
            river = seg["river"]
            from_mile = seg["from_mile"]
            to_mile = seg["to_mile"]
            lo, hi = min(from_mile, to_mile), max(from_mile, to_mile)

            for seg_id, seg_def in USDA_SEGMENT_DEFINITIONS.items():
                if river.upper() == seg_def["river"].upper():
                    seg_lo = seg_def["mile_start"]
                    seg_hi = seg_def["mile_end"]
                    # Check overlap
                    if lo <= seg_hi and hi >= seg_lo:
                        used_segments.add(seg_id)

            # Also map Ohio River
            if "OHIO" in river.upper():
                used_segments.add(4)
            elif "ILLINOIS" in river.upper():
                used_segments.add(3)
            elif "TENNESSEE" in river.upper():
                used_segments.add(4)  # Use Ohio segment as proxy
            elif "MISSOURI" in river.upper():
                used_segments.add(2)  # Use Mid-Miss as proxy
            elif "ARKANSAS" in river.upper():
                used_segments.add(5)  # Use Cairo-Memphis as proxy

        return sorted(used_segments) if used_segments else [7]  # Default to segment 7

    def _get_forecasted_rate(self, usda_segments: List[int]) -> float:
        """
        Get forecasted barge rate for the given USDA segments.

        Uses most recent 4-week average from rate data, or VAR model forecast.
        Returns weighted average rate in $/ton.
        """
        if self.rate_data is None or self.rate_data.empty:
            return 18.0  # Fallback average

        # Get most recent 4 weeks of data
        recent = self.rate_data.tail(4)

        rates = []
        for seg_id in usda_segments:
            col = f"segment_{seg_id}_rate"
            if col in recent.columns:
                avg_rate = recent[col].mean()
                rates.append(avg_rate)

        if not rates:
            return 18.0  # Fallback

        # Return average across segments the route passes through
        return float(np.mean(rates))

    def get_rate_forecast(self, weeks_ahead: int = 4) -> pd.DataFrame:
        """Get rate forecast for all segments."""
        if self.var_model is not None and self.rate_data is not None:
            try:
                # Use VAR model
                rate_cols = [f"segment_{i}_rate" for i in range(1, 8)]
                recent = self.rate_data[rate_cols].tail(3).values
                forecast = self.var_model.forecast(recent, steps=weeks_ahead)
                dates = pd.date_range(
                    self.rate_data['date'].max(),
                    periods=weeks_ahead + 1,
                    freq='W'
                )[1:]
                return pd.DataFrame(forecast, columns=rate_cols, index=dates)
            except Exception:
                pass

        # Fallback: return recent actuals
        if self.rate_data is not None:
            rate_cols = [f"segment_{i}_rate" for i in range(1, 8)]
            return self.rate_data[rate_cols].tail(weeks_ahead)
        return pd.DataFrame()

    # ------------------------------------------------------------------
    # Convenience methods
    # ------------------------------------------------------------------

    def get_route_summary(self, result: RouteResult) -> str:
        """Get a printable summary of a route calculation."""
        lines = []
        lines.append("=" * 70)
        lines.append("BARGE ROUTE COST CALCULATOR")
        lines.append("=" * 70)

        lines.append(f"\nORIGIN:      {result.origin_river}, Mile {result.origin_mile:.1f}")
        lines.append(f"DESTINATION: {result.dest_river}, Mile {result.dest_mile:.1f}")

        lines.append(f"\n--- ROUTE ---")
        lines.append(f"Total Distance:     {result.total_distance_miles:,.1f} miles")
        for seg in result.segments:
            direction = seg['direction']
            lines.append(
                f"  {seg['river']}: Mile {seg['from_mile']:.0f} -> {seg['to_mile']:.0f} "
                f"({seg['distance']:.1f} mi, {direction}, {seg['num_locks']} locks)"
            )

        lines.append(f"\n--- LOCKS ({len(result.locks_encountered)} total) ---")
        for seg in result.segments:
            if seg['locks']:
                lines.append(f"  {seg['river']}:")
                for lock in seg['locks']:
                    lines.append(
                        f"    Mile {lock['mile']:>7.1f}: {lock['name']} "
                        f"({lock['length_ft']:.0f}ft, ~{lock['delay_hrs']:.1f}hr delay)"
                    )

        lines.append(f"\n--- TRANSIT TIME ---")
        lines.append(f"Transit Time:       {result.transit_time_hours:,.1f} hours")
        lines.append(f"Lock Delays:        {result.lock_delay_hours:,.1f} hours")
        lines.append(f"Total Time:         {result.total_time_hours:,.1f} hours ({result.total_time_days:.1f} days)")

        lines.append(f"\n--- BARGE RATE (USDA Tariff Method) ---")
        seg_names = [USDA_SEGMENT_DEFINITIONS.get(s, {}).get('name', f'Seg {s}')
                     for s in result.usda_segments_used]
        lines.append(f"Rate Zones Used:    {', '.join(seg_names)}")
        lines.append(f"Base Rate:          ${result.forecasted_rate_per_ton:.2f}/ton")
        lines.append(f"+ Markup:           ${self.USDA_MARKUP_PER_TON:.2f}/ton")
        lines.append(f"Total Rate:         ${result.rate_plus_markup:.2f}/ton")
        lines.append(f"Per Ton-Mile:       ${result.cost_per_ton_mile:.4f}/ton-mile")

        lines.append(f"\n--- BARGE vs RAIL COMPARISON ---")
        lines.append(f"                    {'Barge':>12}  {'Rail':>12}  {'Savings':>12}")
        lines.append(f"  Per ton-mile:     ${result.cost_per_ton_mile:>11.4f}  ${result.rail_cost_per_ton_mile:>11.4f}  ${result.rail_cost_per_ton_mile - result.cost_per_ton_mile:>11.4f}")
        lines.append(f"  Per ton:          ${result.total_cost_per_ton:>11.2f}  ${result.rail_cost_per_ton:>11.2f}  ${result.barge_savings_per_ton:>11.2f}")
        lines.append(f"  Savings:          {result.barge_savings_pct:>11.1f}%")

        lines.append(f"\n--- OPERATIONAL COSTS (Full {self.BARGES_PER_TOW}-Barge Tow, {self.TOTAL_TOW_TONS:,} tons) ---")
        lines.append(f"  Fuel:             ${result.fuel_cost:>12,.2f}")
        lines.append(f"  Crew:             ${result.crew_cost:>12,.2f}")
        lines.append(f"  Lock Fees:        ${result.lock_fees:>12,.2f}")
        lines.append(f"  TOTAL:            ${result.total_operational_cost:>12,.2f}")
        lines.append(f"  Per Ton:          ${result.cost_per_ton_operational:>12.2f}")

        lines.append("\n" + "=" * 70)
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Loading data...")
    calc = BargeCostCalculator()
    status = calc.load_data()
    for k, v in status.items():
        print(f"  {k}: {v}")

    print("\n" + "=" * 70)
    print("TEST 1: Illinois River Mile 231 -> Mississippi River Mile 100 (Lower Miss)")
    print("=" * 70)
    result = calc.calculate_route_cost(
        origin_river="ILLINOIS RIVER",
        origin_mile=231,
        dest_river="MISSISSIPPI RIVER",
        dest_mile=100,
    )
    print(calc.get_route_summary(result))

    print("\n" + "=" * 70)
    print("TEST 2: Upper Mississippi Mile 800 -> Mississippi Mile 100 (Gulf)")
    print("=" * 70)
    result2 = calc.calculate_route_cost(
        origin_river="MISSISSIPPI RIVER",
        origin_mile=800,
        dest_river="MISSISSIPPI RIVER",
        dest_mile=100,
    )
    print(calc.get_route_summary(result2))

    print("\n" + "=" * 70)
    print("TEST 3: Ohio River Mile 500 -> Mississippi River Mile 200")
    print("=" * 70)
    result3 = calc.calculate_route_cost(
        origin_river="OHIO RIVER",
        origin_mile=500,
        dest_river="MISSISSIPPI RIVER",
        dest_mile=200,
    )
    print(calc.get_route_summary(result3))
