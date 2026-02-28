"""
Combined Import + Export Cargo ↔ MRTIS Vessel Matching
=======================================================
Matches MRTIS voyage segments against BOTH import and export manifests using:

  Physical draft-change logic to determine operation direction:
    DraftDeltaFt < -DRAFT_THRESHOLD  → DISCHARGE (imports)
      vessel arrived deep (laden), departed lighter
    DraftDeltaFt > +DRAFT_THRESHOLD  → LOADING   (exports)
      vessel arrived light (ballast), departed deep (laden)
    CargoStatus field confirms / resolves ambiguous cases

  Date matching:
    DISCHARGE → manifest Arrival Date   ↔  FirstTerminalArrivalTime   ± window_days
    LOADING   → export  Shipment Date   ↔  FirstTerminalDepartureTime ± window_days
                (fallback: FirstTerminalArrivalTime if departure time missing)

Outputs (written to --output directory):
    voyage_segments_cargo_enriched.csv  — segments + Import + Export match columns
    cargo_match_detail.csv              — one row per matched BOL (Direction col)
    facility_cargo_summary.csv          — per-facility cargo totals (main ask)
    cargo_match_report.txt              — statistics

Usage:
    python cargo_matcher.py ^
        --segments   "G:/My Drive/LLM/project_mrtis/results_2025_review/voyage_segments.csv" ^
        --imports    "G:/My Drive/LLM/project_manifest/PIPELINE/phase_07_enrichment/phase_07_output.csv" ^
        --exports    "G:/My Drive/LLM/project_manifest/PIPELINE_EXPORTS/phase_07_enrichment/phase_07_output.csv" ^
        --zones      "G:/My Drive/LLM/project_mrtis/terminal_zone_dictionary.csv" ^
        --output     "G:/My Drive/LLM/project_mrtis/results_2025_review/"

Author: WSD3 / Claude Code  v1.0.0
"""

import sys
import csv
import logging
import argparse
from pathlib import Path
from datetime import datetime, date, timedelta
from collections import defaultdict

import pandas as pd

# ── path setup for shared vessel-name utilities ───────────────────────────────
PROJECT_MRTIS = Path(__file__).parent.parent / "project_mrtis"
sys.path.insert(0, str(PROJECT_MRTIS))
from src.data.vessel_name_normalizer import build_name_key

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)

# ── constants ─────────────────────────────────────────────────────────────────
DRAFT_THRESHOLD_FT = 2.0     # minimum draft change to infer loading/discharging
DEFAULT_WINDOW     = 3        # ±calendar days for manifest date match

IMPORT_COLS = [
    'Arrival Date', 'Vessel', 'IMO', 'Tons',
    'Group', 'Commodity', 'Cargo', 'Cargo_Detail',
    'Country of Origin (F)', 'Shipper', 'Consignee',
    'Bill of Lading Number', 'Port_Consolidated',
]

EXPORT_COLS = [
    'Arrival Date',   # = Shipment Date in exports
    'Vessel', 'IMO', 'Tons',
    'Group', 'Commodity', 'Cargo', 'Cargo_Detail',
    'Country of Origin (F)',  # = destination country in exports
    'Shipper',                # = U.S. exporter
    'Bill of Lading Number', 'Port_Consolidated',
]

# Columns written to enriched segment file
IMPORT_RESULT_COLS = [
    'ImportMatchStatus', 'ImportMatchKey', 'ImportBOLCount',
    'ImportTotalTons', 'ImportGroup', 'ImportCommodity',
    'ImportCargo', 'ImportCargoDetail', 'ImportOrigins',
    'ImportShippers', 'ImportArrivalDate', 'ImportTimeDeltaDays',
]
EXPORT_RESULT_COLS = [
    'ExportMatchStatus', 'ExportMatchKey', 'ExportBOLCount',
    'ExportTotalTons', 'ExportGroup', 'ExportCommodity',
    'ExportCargo', 'ExportCargoDetail', 'ExportDestinations',
    'ExportShippers', 'ExportShipmentDate', 'ExportTimeDeltaDays',
]
OPERATION_COLS = ['OperationType', 'DraftClassification']


# ══════════════════════════════════════════════════════════════════════════════
# MANIFEST INDEX — reusable for both imports and exports
# ══════════════════════════════════════════════════════════════════════════════

class ManifestIndex:
    """Loads a classified manifest CSV and builds vessel lookup indices.

    For imports:  filter to Port_Consolidated = 'New Orleans'
    For exports:  filter to Port_Consolidated in ('Mississippi River','New Orleans')
    """

    def __init__(self, path: Path, direction: str, port_filter: list[str]):
        self.path = path
        self.direction = direction  # 'IMPORT' or 'EXPORT'
        self.port_filter = port_filter
        self.imo_index: dict[str, list[dict]] = defaultdict(list)
        self.name_index: dict[str, list[dict]] = defaultdict(list)
        self.total_loaded = 0
        self._load()

    def _load(self):
        cols = IMPORT_COLS if self.direction == 'IMPORT' else EXPORT_COLS
        available = None
        try:
            # peek at columns first
            peek = pd.read_csv(self.path, nrows=0)
            available = [c for c in cols if c in peek.columns]
        except Exception:
            available = cols

        log.info(f"  Loading {self.direction} manifest from {self.path.name}")
        df = pd.read_csv(
            self.path, usecols=available, dtype={'IMO': str}, low_memory=False
        )
        log.info(f"    Total records: {len(df):,}")

        # Port filter
        df = df[df['Port_Consolidated'].isin(self.port_filter)].copy()
        log.info(f"    After port filter {self.port_filter}: {len(df):,}")

        # Remove excluded exports (Group == 'EXCLUDED')
        if 'Group' in df.columns:
            df = df[df['Group'] != 'EXCLUDED'].copy()
            log.info(f"    After excluding EXCLUDED group: {len(df):,}")

        # Parse date
        df['_date'] = pd.to_datetime(df['Arrival Date'], errors='coerce').dt.date
        df['_imo'] = df['IMO'].fillna('').astype(str).str.strip()
        df.loc[~df['_imo'].str.match(r'^\d+$'), '_imo'] = ''
        df['_nk'] = df['Vessel'].apply(
            lambda v: build_name_key(v) if pd.notna(v) else ''
        )

        records = df.to_dict('records')
        self.total_loaded = len(records)

        for rec in records:
            if not rec.get('_date'):
                continue
            imo = rec['_imo']
            if imo:
                self.imo_index[imo].append(rec)
            nk = rec['_nk']
            if nk:
                self.name_index[nk].append(rec)

        for idx in (self.imo_index, self.name_index):
            for k in idx:
                idx[k].sort(key=lambda r: r['_date'] or date.min)

        log.info(
            f"    Indexed {self.total_loaded:,}: "
            f"{len(self.imo_index):,} IMOs, {len(self.name_index):,} name keys"
        )

    def find(self, imo: str, vessel_name: str,
             ref_date: date, window: int) -> tuple[list[dict], str]:
        """Return (matching records, match_key)."""
        lo = ref_date - timedelta(days=window)
        hi = ref_date + timedelta(days=window)

        def _win(recs):
            return [r for r in recs if r.get('_date') and lo <= r['_date'] <= hi]

        imo_c = str(imo).strip() if imo else ''
        if imo_c and imo_c in self.imo_index:
            hits = _win(self.imo_index[imo_c])
            if hits:
                return hits, 'IMO'

        nk = build_name_key(vessel_name)
        if nk and nk in self.name_index:
            hits = _win(self.name_index[nk])
            if hits:
                return hits, 'NAME'

        return [], ''


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _parse_dt(s: str) -> date | None:
    """Parse '2025-01-15 22:50:00' → date."""
    if not s or not str(s).strip():
        return None
    try:
        return datetime.strptime(str(s).strip(), '%Y-%m-%d %H:%M:%S').date()
    except ValueError:
        return None


def _parse_draft(s) -> float | None:
    try:
        v = float(s)
        return v if v > 0 else None
    except (ValueError, TypeError):
        return None


def _classify_operation(row: dict) -> tuple[str, str]:
    """
    Returns (OperationType, DraftClassification).

    OperationType:     DISCHARGE | LOADING | BALLAST | UNKNOWN
    DraftClassification: source of determination
    """
    cargo_status = str(row.get('CargoStatus', '')).strip()
    draft_delta  = _parse_draft(row.get('DraftDeltaFt', ''))
    arr_draft    = _parse_draft(row.get('FirstTerminalArrivalDraft', ''))
    dep_draft    = _parse_draft(row.get('FirstTerminalDepartureDraft', ''))

    # ── 1. Use CargoStatus as primary signal ─────────────────────────────────
    if cargo_status == 'Laden Inbound':
        # Arrived heavy → discharging
        return 'DISCHARGE', 'CargoStatus=Laden Inbound'
    if cargo_status == 'Laden Outbound':
        # Departed heavy → loading
        return 'LOADING', 'CargoStatus=Laden Outbound'
    if cargo_status == 'Ballast':
        # Both drafts light — but could still be handling cargo if draft is non-trivial
        # Use draft delta as tiebreak
        if draft_delta is not None:
            if draft_delta > DRAFT_THRESHOLD_FT:
                return 'LOADING', f'Ballast+DraftDelta={draft_delta:+.1f}ft'
            if draft_delta < -DRAFT_THRESHOLD_FT:
                return 'DISCHARGE', f'Ballast+DraftDelta={draft_delta:+.1f}ft'
        return 'BALLAST', 'CargoStatus=Ballast'

    # ── 2. Fallback: draft delta ──────────────────────────────────────────────
    if draft_delta is not None:
        if draft_delta > DRAFT_THRESHOLD_FT:
            return 'LOADING', f'DraftDelta={draft_delta:+.1f}ft'
        if draft_delta < -DRAFT_THRESHOLD_FT:
            return 'DISCHARGE', f'DraftDelta={draft_delta:+.1f}ft'

    # ── 3. Individual arrival/departure drafts ────────────────────────────────
    if arr_draft and dep_draft:
        diff = dep_draft - arr_draft
        if diff > DRAFT_THRESHOLD_FT:
            return 'LOADING', f'ArrDraft={arr_draft:.1f}ft DepDraft={dep_draft:.1f}ft'
        if diff < -DRAFT_THRESHOLD_FT:
            return 'DISCHARGE', f'ArrDraft={arr_draft:.1f}ft DepDraft={dep_draft:.1f}ft'
        # Very small change — not conclusive
        if arr_draft > 20:   # anything over 20 ft is clearly laden for inland vessels
            return 'DISCHARGE', f'ArrDraft={arr_draft:.1f}ft (deep, minimal change)'

    return 'UNKNOWN', 'Insufficient draft data'


def _aggregate(matches: list[dict], direction: str) -> dict:
    """Aggregate a list of manifest BOL dicts into summary fields."""
    bols = set()
    tons = 0.0
    groups, comms, cargos, details, origins, shippers, dates = [], [], [], [], [], [], []

    for m in matches:
        bol = m.get('Bill of Lading Number', '')
        if bol:
            bols.add(str(bol))
        try:
            t = float(m.get('Tons', 0))
            if t > 0:
                tons += t
        except (ValueError, TypeError):
            pass
        for val, lst in [
            (m.get('Group', ''),                  groups),
            (m.get('Commodity', ''),              comms),
            (m.get('Cargo', ''),                  cargos),
            (m.get('Cargo_Detail', ''),            details),
            (m.get('Country of Origin (F)', ''), origins),
            (m.get('Shipper', ''),                shippers),
        ]:
            if pd.notna(val) and str(val).strip() and str(val).strip() not in lst:
                lst.append(str(val).strip())
        d = m.get('_date')
        if d:
            dates.append(d)

    shippers = shippers[:3] + ([f'(+{len(shippers)-3} more)'] if len(shippers) > 3 else [])

    if direction == 'IMPORT':
        return {
            'ImportBOLCount':    len(bols),
            'ImportTotalTons':   round(tons, 2) if tons > 0 else '',
            'ImportGroup':       ', '.join(groups),
            'ImportCommodity':   ', '.join(comms),
            'ImportCargo':       ', '.join(cargos),
            'ImportCargoDetail': ', '.join(details),
            'ImportOrigins':     ', '.join(origins),
            'ImportShippers':    ', '.join(shippers),
            'ImportArrivalDate': min(dates).isoformat() if dates else '',
        }
    else:
        return {
            'ExportBOLCount':     len(bols),
            'ExportTotalTons':    round(tons, 2) if tons > 0 else '',
            'ExportGroup':        ', '.join(groups),
            'ExportCommodity':    ', '.join(comms),
            'ExportCargo':        ', '.join(cargos),
            'ExportCargoDetail':  ', '.join(details),
            'ExportDestinations': ', '.join(origins),   # destination country for exports
            'ExportShippers':     ', '.join(shippers),
            'ExportShipmentDate': min(dates).isoformat() if dates else '',
        }


def _empty(direction: str, status: str) -> dict:
    if direction == 'IMPORT':
        return {
            'ImportMatchStatus': status, 'ImportMatchKey': '',
            'ImportBOLCount': '', 'ImportTotalTons': '',
            'ImportGroup': '', 'ImportCommodity': '', 'ImportCargo': '',
            'ImportCargoDetail': '', 'ImportOrigins': '', 'ImportShippers': '',
            'ImportArrivalDate': '', 'ImportTimeDeltaDays': '',
        }
    else:
        return {
            'ExportMatchStatus': status, 'ExportMatchKey': '',
            'ExportBOLCount': '', 'ExportTotalTons': '',
            'ExportGroup': '', 'ExportCommodity': '', 'ExportCargo': '',
            'ExportCargoDetail': '', 'ExportDestinations': '', 'ExportShippers': '',
            'ExportShipmentDate': '', 'ExportTimeDeltaDays': '',
        }


def _load_zones(path: Path) -> tuple[set[str], set[str]]:
    """Return (discharge_zones, load_zones) from terminal_zone_dictionary."""
    discharge, load = set(), set()
    with open(path, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            act = row.get('Activity', '').strip()
            zone = row['Zone'].strip()
            if act in ('Discharge - Only', 'Load or Discharge'):
                discharge.add(zone)
            if act in ('Load - Only', 'Load or Discharge'):
                load.add(zone)
    return discharge, load


# ══════════════════════════════════════════════════════════════════════════════
# MAIN MATCHER
# ══════════════════════════════════════════════════════════════════════════════

class CargoMatcher:

    def __init__(self, imp_index: ManifestIndex, exp_index: ManifestIndex,
                 discharge_zones: set[str], load_zones: set[str],
                 window_days: int = DEFAULT_WINDOW):
        self.imp = imp_index
        self.exp = exp_index
        self.discharge_zones = discharge_zones
        self.load_zones = load_zones
        self.window = window_days

        # counters
        self.stats = defaultdict(int)
        self.imp_tonnage_facility: dict[str, float] = defaultdict(float)
        self.exp_tonnage_facility: dict[str, float] = defaultdict(float)
        self.imp_commodity_facility: dict[tuple, float] = defaultdict(float)
        self.exp_commodity_facility: dict[tuple, float] = defaultdict(float)
        self.detail_rows: list[dict] = []

    def _match_one(self, seg: dict, direction: str, ref_date: date) -> dict:
        """Match a segment against one manifest index. Returns result columns."""
        idx = self.imp if direction == 'IMPORT' else self.exp
        imo  = seg.get('IMO', '')
        name = seg.get('VesselName', '')
        zone = seg.get('DischargeTerminalZone', '')

        matches, key = idx.find(imo, name, ref_date, self.window)
        if not matches:
            return _empty(direction, 'UNMATCHED')

        agg = _aggregate(matches, direction)
        nearest = min(matches, key=lambda m: abs((m['_date'] - ref_date).days))
        delta = (nearest['_date'] - ref_date).days

        result = _empty(direction, 'MATCHED')  # build empty template then fill
        if direction == 'IMPORT':
            result.update(agg)
            result['ImportMatchStatus'] = 'MATCHED'
            result['ImportMatchKey'] = key
            result['ImportTimeDeltaDays'] = delta
        else:
            result.update(agg)
            result['ExportMatchStatus'] = 'MATCHED'
            result['ExportMatchKey'] = key
            result['ExportTimeDeltaDays'] = delta

        self.stats[f'{direction}_matched'] += 1
        if key == 'IMO':
            self.stats[f'{direction}_by_imo'] += 1
        else:
            self.stats[f'{direction}_by_name'] += 1

        # per-facility tonnage tracking
        facility = seg.get('DischargeTerminalFacility', zone)
        for m in matches:
            try:
                t = float(m.get('Tons', 0))
            except (ValueError, TypeError):
                t = 0.0
            comm = str(m.get('Commodity', 'Unknown'))
            cargo_grp = str(m.get('Group', 'Unknown'))
            if direction == 'IMPORT':
                self.imp_tonnage_facility[facility] += t
                self.imp_commodity_facility[(facility, cargo_grp, comm)] += t
            else:
                self.exp_tonnage_facility[facility] += t
                self.exp_commodity_facility[(facility, cargo_grp, comm)] += t

        # detail rows
        for m in matches:
            try:
                t = float(m.get('Tons', 0))
            except (ValueError, TypeError):
                t = ''
            self.detail_rows.append({
                'VoyageID':            seg.get('VoyageID', ''),
                'VesselName':          name,
                'IMO':                 imo,
                'Direction':           direction,
                'TerminalZone':        zone,
                'TerminalFacility':    facility,
                'OperationType':       seg.get('_op_type', ''),
                'DraftClassification': seg.get('_draft_class', ''),
                'FirstTerminalArrivalTime':   seg.get('FirstTerminalArrivalTime', ''),
                'FirstTerminalDepartureTime': seg.get('FirstTerminalDepartureTime', ''),
                'ArrivalDraft_ft':     seg.get('FirstTerminalArrivalDraft', ''),
                'DepartureDraft_ft':   seg.get('FirstTerminalDepartureDraft', ''),
                'DraftDeltaFt':        seg.get('DraftDeltaFt', ''),
                'MatchKey':            key,
                'BillOfLading':        m.get('Bill of Lading Number', ''),
                'ManifestDate':        m['_date'].isoformat() if m.get('_date') else '',
                'TimeDeltaDays':       delta,
                'Group':               m.get('Group', '') if pd.notna(m.get('Group')) else '',
                'Commodity':           m.get('Commodity', '') if pd.notna(m.get('Commodity')) else '',
                'Cargo':               m.get('Cargo', '') if pd.notna(m.get('Cargo')) else '',
                'Cargo_Detail':        m.get('Cargo_Detail', '') if pd.notna(m.get('Cargo_Detail')) else '',
                'Tons':                t,
                'CountryField':        m.get('Country of Origin (F)', '') if pd.notna(m.get('Country of Origin (F)')) else '',
                'Shipper':             m.get('Shipper', '') if pd.notna(m.get('Shipper')) else '',
                'Consignee':           m.get('Consignee', '') if pd.notna(m.get('Consignee')) else '',
            })

        return result

    def process(self, segments_path: Path) -> tuple[list[dict], list[str]]:
        """Process all voyage segments. Returns (enriched rows, original column names)."""
        log.info(f"Reading segments from {segments_path}")
        with open(segments_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            orig_cols = list(reader.fieldnames)
            segments = list(reader)
        log.info(f"  Total segments: {len(segments):,}")
        self.stats['total'] = len(segments)

        enriched = []

        for seg in segments:
            row = dict(seg)
            zone = seg.get('DischargeTerminalZone', '').strip()

            # Classify operation from draft + CargoStatus
            op_type, draft_class = _classify_operation(seg)
            row['OperationType'] = op_type
            row['DraftClassification'] = draft_class
            seg['_op_type'] = op_type
            seg['_draft_class'] = draft_class

            # Check if zone is actionable
            in_discharge_zone = zone and zone in self.discharge_zones
            in_load_zone = zone and zone in self.load_zones

            if not zone or (not in_discharge_zone and not in_load_zone):
                row.update(_empty('IMPORT', 'NOT_CARGO_ZONE'))
                row.update(_empty('EXPORT', 'NOT_CARGO_ZONE'))
                self.stats['not_cargo_zone'] += 1
                enriched.append(row)
                continue

            self.stats['cargo_zone_visits'] += 1

            arr_date = _parse_dt(seg.get('FirstTerminalArrivalTime', ''))
            dep_date = _parse_dt(seg.get('FirstTerminalDepartureTime', ''))

            # ── DISCHARGE matching (imports) ──────────────────────────────────
            if op_type in ('DISCHARGE', 'UNKNOWN') and in_discharge_zone:
                if arr_date:
                    result = self._match_one(seg, 'IMPORT', arr_date)
                else:
                    result = _empty('IMPORT', 'NO_ARRIVAL_TIME')
                    self.stats['import_no_time'] += 1
            else:
                result = _empty('IMPORT', 'NOT_DISCHARGE_OP')
            row.update(result)

            # ── LOADING matching (exports) ────────────────────────────────────
            if op_type in ('LOADING', 'UNKNOWN') and in_load_zone:
                # Use departure time for exports (when BOL is issued after loading)
                ref = dep_date or arr_date
                if ref:
                    result = self._match_one(seg, 'EXPORT', ref)
                else:
                    result = _empty('EXPORT', 'NO_DEPARTURE_TIME')
                    self.stats['export_no_time'] += 1
            else:
                result = _empty('EXPORT', 'NOT_LOADING_OP')
            row.update(result)

            enriched.append(row)

        # log summary
        log.info(f"  Cargo zone visits:   {self.stats['cargo_zone_visits']:,}")
        log.info(f"  Import matched:      {self.stats['IMPORT_matched']:,}  "
                 f"(IMO: {self.stats['IMPORT_by_imo']:,}, NAME: {self.stats['IMPORT_by_name']:,})")
        log.info(f"  Export matched:      {self.stats['EXPORT_matched']:,}  "
                 f"(IMO: {self.stats['EXPORT_by_imo']:,}, NAME: {self.stats['EXPORT_by_name']:,})")

        return enriched, orig_cols

    # ── writers ───────────────────────────────────────────────────────────────

    def write_enriched(self, enriched, orig_cols, path: Path):
        all_cols = (list(orig_cols) + OPERATION_COLS +
                    IMPORT_RESULT_COLS + EXPORT_RESULT_COLS)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', newline='', encoding='utf-8') as f:
            csv.DictWriter(f, fieldnames=all_cols,
                           extrasaction='ignore').writeheader()
            csv.DictWriter(f, fieldnames=all_cols,
                           extrasaction='ignore').writerows(enriched)
        log.info(f"Wrote enriched segments: {path} ({len(enriched):,} rows)")

    def write_detail(self, path: Path):
        if not self.detail_rows:
            log.info("No detail rows to write.")
            return
        cols = [
            'VoyageID', 'VesselName', 'IMO', 'Direction',
            'TerminalZone', 'TerminalFacility', 'OperationType', 'DraftClassification',
            'FirstTerminalArrivalTime', 'FirstTerminalDepartureTime',
            'ArrivalDraft_ft', 'DepartureDraft_ft', 'DraftDeltaFt',
            'MatchKey', 'BillOfLading', 'ManifestDate', 'TimeDeltaDays',
            'Group', 'Commodity', 'Cargo', 'Cargo_Detail',
            'Tons', 'CountryField', 'Shipper', 'Consignee',
        ]
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(self.detail_rows)
        log.info(f"Wrote match detail: {path} ({len(self.detail_rows):,} rows)")

    def write_facility_summary(self, path: Path):
        """Per-facility cargo summary — the key analytical output."""
        all_keys = set(self.imp_commodity_facility) | set(self.exp_commodity_facility)
        if not all_keys:
            log.info("No facility data to summarize.")
            return

        rows = []
        for (facility, group, comm) in sorted(all_keys):
            imp_t = self.imp_commodity_facility.get((facility, group, comm), 0.0)
            exp_t = self.exp_commodity_facility.get((facility, group, comm), 0.0)
            rows.append({
                'Facility':         facility,
                'Group':            group,
                'Commodity':        comm,
                'ImportTons':       round(imp_t, 0) if imp_t > 0 else '',
                'ExportTons':       round(exp_t, 0) if exp_t > 0 else '',
                'TotalTons':        round(imp_t + exp_t, 0),
                'Direction':        ('Both' if imp_t > 0 and exp_t > 0 else
                                     'Import' if imp_t > 0 else 'Export'),
            })

        # Sort by total tonnage descending
        rows.sort(key=lambda r: r['TotalTons'], reverse=True)

        path.parent.mkdir(parents=True, exist_ok=True)
        cols = ['Facility', 'Group', 'Commodity',
                'ImportTons', 'ExportTons', 'TotalTons', 'Direction']
        with open(path, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
        log.info(f"Wrote facility summary: {path} ({len(rows):,} rows)")

    def write_report(self, path: Path):
        s = self.stats
        total_imp = sum(self.imp_tonnage_facility.values())
        total_exp = sum(self.exp_tonnage_facility.values())

        lines = [
            "=" * 70,
            "Combined Import + Export Cargo ↔ MRTIS Vessel Matching Report",
            f"Generated: {datetime.now():%Y-%m-%d %H:%M:%S}",
            f"Match window: ±{self.window} days  |  Draft threshold: {DRAFT_THRESHOLD_FT} ft",
            "=" * 70,
            "",
            "SEGMENT OVERVIEW",
            "-" * 40,
            f"  Total segments:         {s['total']:>8,}",
            f"  Not in cargo zone:      {s['not_cargo_zone']:>8,}",
            f"  Cargo zone visits:      {s['cargo_zone_visits']:>8,}",
            "",
            "OPERATION TYPE CLASSIFICATION (draft-based)",
            "-" * 40,
        ]

        # Count op types from stats (not directly stored, so compute from detail rows)
        op_counts: dict[str, int] = defaultdict(int)
        for r in self.detail_rows:
            op_counts[r['OperationType']] += 1

        for op, cnt in sorted(op_counts.items(), key=lambda x: -x[1]):
            lines.append(f"  {op:<20} {cnt:>6,} BOL rows")

        lines += [
            "",
            "IMPORT MATCHING (discharge events)",
            "-" * 40,
            f"  Matched:                {s['IMPORT_matched']:>8,}",
            f"    by IMO:               {s['IMPORT_by_imo']:>8,}",
            f"    by vessel name:       {s['IMPORT_by_name']:>8,}",
            f"  Matched tonnage:        {total_imp/1e6:>8.2f}M tons",
            "",
            "EXPORT MATCHING (loading events)",
            "-" * 40,
            f"  Matched:                {s['EXPORT_matched']:>8,}",
            f"    by IMO:               {s['EXPORT_by_imo']:>8,}",
            f"    by vessel name:       {s['EXPORT_by_name']:>8,}",
            f"  Matched tonnage:        {total_exp/1e6:>8.2f}M tons",
            "",
            "TOP FACILITIES — IMPORTS (by tonnage)",
            "-" * 40,
        ]
        for fac, t in sorted(self.imp_tonnage_facility.items(), key=lambda x: -x[1])[:20]:
            lines.append(f"  {fac:<45} {t/1e3:>10,.0f}K tons")

        lines += [
            "",
            "TOP FACILITIES — EXPORTS (by tonnage)",
            "-" * 40,
        ]
        for fac, t in sorted(self.exp_tonnage_facility.items(), key=lambda x: -x[1])[:20]:
            lines.append(f"  {fac:<45} {t/1e3:>10,.0f}K tons")

        lines += [
            "",
            "IMPORT COMMODITIES (across all facilities)",
            "-" * 40,
        ]
        imp_comm: dict[str, float] = defaultdict(float)
        for (_, g, c), t in self.imp_commodity_facility.items():
            imp_comm[f"{g} / {c}"] += t
        for k, t in sorted(imp_comm.items(), key=lambda x: -x[1])[:15]:
            lines.append(f"  {k:<45} {t/1e3:>10,.0f}K tons")

        lines += [
            "",
            "EXPORT COMMODITIES (across all facilities)",
            "-" * 40,
        ]
        exp_comm: dict[str, float] = defaultdict(float)
        for (_, g, c), t in self.exp_commodity_facility.items():
            exp_comm[f"{g} / {c}"] += t
        for k, t in sorted(exp_comm.items(), key=lambda x: -x[1])[:15]:
            lines.append(f"  {k:<45} {t/1e3:>10,.0f}K tons")

        lines.append("")

        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        log.info(f"Wrote cargo match report: {path}")


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description='Combined Import+Export Cargo ↔ MRTIS Vessel Matching')
    parser.add_argument('--segments', required=True,
                        help='voyage_segments.csv path')
    parser.add_argument('--imports',  required=True,
                        help='Import phase_07_output.csv path')
    parser.add_argument('--exports',  required=True,
                        help='Export phase_07_output.csv path')
    parser.add_argument('--zones',    required=True,
                        help='terminal_zone_dictionary.csv path')
    parser.add_argument('--output',   required=True,
                        help='Output directory')
    parser.add_argument('--window', type=int, default=DEFAULT_WINDOW,
                        help=f'Match window ±days (default {DEFAULT_WINDOW})')
    args = parser.parse_args()

    log.info("=" * 60)
    log.info("Combined Cargo ↔ MRTIS Matching")
    log.info(f"Window: ±{args.window} days  |  Draft threshold: {DRAFT_THRESHOLD_FT} ft")
    log.info("=" * 60)

    # Load manifest indices
    log.info("\nLoading manifests...")
    imp_idx = ManifestIndex(
        Path(args.imports), 'IMPORT',
        port_filter=['New Orleans']
    )
    exp_idx = ManifestIndex(
        Path(args.exports), 'EXPORT',
        port_filter=['Mississippi River', 'New Orleans']
    )

    # Load zone dictionaries
    discharge_zones, load_zones = _load_zones(Path(args.zones))
    log.info(f"\nZones: {len(discharge_zones)} discharge, {len(load_zones)} load")

    # Run matching
    matcher = CargoMatcher(imp_idx, exp_idx, discharge_zones, load_zones, args.window)
    enriched, orig_cols = matcher.process(Path(args.segments))

    # Write outputs
    out = Path(args.output)
    matcher.write_enriched(enriched, orig_cols,
                           out / 'voyage_segments_cargo_enriched.csv')
    matcher.write_detail(out / 'cargo_match_detail.csv')
    matcher.write_facility_summary(out / 'facility_cargo_summary.csv')
    matcher.write_report(out / 'cargo_match_report.txt')

    log.info("\n" + "=" * 60)
    log.info("Done.")


if __name__ == '__main__':
    main()
