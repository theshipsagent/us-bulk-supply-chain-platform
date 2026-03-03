"""
Vessel Parameter Resolver
==========================
Resolves vessel physical parameters (GRT, draft, LOA, beam, DWT) needed for
pilotage rate calculations. Uses a local-first, web-fallback lookup chain with
DuckDB caching so repeat queries are instant.

Lookup order
------------
1. Local ships_register.csv     (52K vessels, IMO-keyed, always tried first)
2. DuckDB cache                 (previous web lookups persisted locally)
3. Equasis.org scrape           (free EMSA database — most authoritative)
4. MarineTraffic.com scrape     (public vessel detail pages — secondary)
5. Soft fail                    (returns VesselParams with available fields,
                                 raises VesselNotFoundError with instructions
                                 if GRT and draft are both missing)

Usage
-----
    from vessel_resolver import resolve_vessel, VesselParams

    params = resolve_vessel(imo="9123456")
    params = resolve_vessel(name="OCEAN PIONEER")   # name-based fallback
    params = resolve_vessel(grt=35000, draft_m=12.0) # manual override
"""

from __future__ import annotations

import csv
import json
import logging
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_MODULE_DIR = Path(__file__).parent.parent
_DATA_DIR = _MODULE_DIR / "data"
_CACHE_FILE = _DATA_DIR / "vessel_cache.json"

# Ships register lives in 02_TOOLSETS/vessel_intelligence/
# parents[3] = 02_TOOLSETS/
_SHIPS_REGISTER = (
    Path(__file__).parents[3]
    / "vessel_intelligence"
    / "data"
    / "ships_register.csv"
)

_SCRAPE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

_SCRAPE_TIMEOUT = 15  # seconds


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class VesselParams:
    """Physical parameters of a vessel used in pilotage calculations."""

    imo: Optional[str] = None
    name: Optional[str] = None
    vessel_type: Optional[str] = None
    flag: Optional[str] = None

    # Tonnage
    grt: Optional[int] = None       # Gross Registered Tons (GT) — primary for GRT-tier pilots
    nrt: Optional[int] = None       # Net Registered Tons
    dwt: Optional[int] = None       # Deadweight Tons

    # Dimensions (metric)
    loa_m: Optional[float] = None   # Length Over All (metres)
    beam_m: Optional[float] = None  # Beam (metres)
    draft_m: Optional[float] = None # Scantling/design draft (metres)

    # Derived (set automatically)
    draft_ft: Optional[float] = None  # Draft in feet (for draft-per-foot calculations)

    # Metadata
    source: str = "unknown"         # "local_register" | "cache" | "equasis" | "marinetraffic" | "manual"
    source_url: Optional[str] = None
    lookup_timestamp: Optional[str] = None
    confidence: str = "high"        # "high" | "medium" | "low"
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.draft_m and self.draft_ft is None:
            self.draft_ft = round(self.draft_m * 3.28084, 2)

    @property
    def is_complete(self) -> bool:
        """True if minimum required fields for pilotage calc are present."""
        return self.grt is not None and self.draft_m is not None

    def to_dict(self) -> dict:
        return {
            "imo": self.imo,
            "name": self.name,
            "vessel_type": self.vessel_type,
            "flag": self.flag,
            "grt": self.grt,
            "nrt": self.nrt,
            "dwt": self.dwt,
            "loa_m": self.loa_m,
            "beam_m": self.beam_m,
            "draft_m": self.draft_m,
            "draft_ft": self.draft_ft,
            "source": self.source,
            "confidence": self.confidence,
            "warnings": self.warnings,
        }


class VesselNotFoundError(Exception):
    """Raised when a vessel cannot be resolved and critical params are missing."""
    pass


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def resolve_vessel(
    imo: Optional[str] = None,
    name: Optional[str] = None,
    grt: Optional[int] = None,
    draft_m: Optional[float] = None,
    dwt: Optional[int] = None,
    loa_m: Optional[float] = None,
    beam_m: Optional[float] = None,
    force_web: bool = False,
) -> VesselParams:
    """Resolve vessel parameters using local-first, web-fallback lookup chain.

    Parameters
    ----------
    imo : str, optional
        IMO vessel number (7 digits, with or without "IMO" prefix).
    name : str, optional
        Vessel name (used if IMO not available — less reliable).
    grt : int, optional
        Manual GRT override — skips lookup if provided together with draft_m.
    draft_m : float, optional
        Manual draft override in metres.
    dwt, loa_m, beam_m : optional
        Additional manual overrides.
    force_web : bool
        Skip local/cache and go straight to web sources.

    Returns
    -------
    VesselParams
        Resolved vessel parameters. Check `.is_complete` and `.warnings`.

    Raises
    ------
    VesselNotFoundError
        If vessel cannot be resolved and GRT + draft are both missing.
    """
    # Manual override — if caller provides GRT and draft, use them directly
    if grt is not None and draft_m is not None and not force_web:
        return VesselParams(
            imo=imo,
            name=name,
            grt=grt,
            draft_m=draft_m,
            dwt=dwt,
            loa_m=loa_m,
            beam_m=beam_m,
            source="manual",
            confidence="high",
        )

    clean_imo = _clean_imo(imo) if imo else None

    # Apply any partial manual overrides at the end
    manual_overrides = {
        k: v for k, v in
        {"grt": grt, "draft_m": draft_m, "dwt": dwt, "loa_m": loa_m, "beam_m": beam_m}.items()
        if v is not None
    }

    params: Optional[VesselParams] = None

    if not force_web:
        # 1. Local ships register
        if clean_imo:
            params = _lookup_local_register(clean_imo)
            if params:
                logger.debug("Vessel %s resolved from local register", clean_imo)

        # 2. DuckDB / JSON cache
        if params is None and clean_imo:
            params = _lookup_cache(clean_imo)
            if params:
                logger.debug("Vessel %s resolved from cache", clean_imo)

        # 3. Name-based local search (slower, fuzzy)
        if params is None and name and not clean_imo:
            params = _lookup_local_by_name(name)

    # 4. Equasis web scrape
    if params is None and clean_imo:
        logger.info("Vessel %s not in local data — trying Equasis.org", clean_imo)
        params = _scrape_equasis(clean_imo)
        if params:
            _write_cache(params)

    # 5. MarineTraffic web scrape
    if params is None and clean_imo:
        logger.info("Equasis miss — trying MarineTraffic for IMO %s", clean_imo)
        params = _scrape_marinetraffic(clean_imo)
        if params:
            _write_cache(params)

    # Apply manual overrides on top of any resolved data
    if params is not None and manual_overrides:
        for k, v in manual_overrides.items():
            setattr(params, k, v)
        params.__post_init__()  # recalc draft_ft if draft_m changed

    if params is None:
        # Build partial params from whatever we have
        if grt is not None or draft_m is not None:
            params = VesselParams(
                imo=clean_imo, name=name, source="manual", confidence="low",
                **manual_overrides,
            )
            params.warnings.append(
                "Vessel not found in any source — using manual parameters only"
            )
        else:
            raise VesselNotFoundError(
                f"Cannot resolve vessel (IMO={imo}, name={name}). "
                "Provide grt= and draft_m= manually, or check the IMO number. "
                "Sources tried: local register, cache, Equasis, MarineTraffic."
            )

    return params


# ---------------------------------------------------------------------------
# Local register lookup
# ---------------------------------------------------------------------------

def _clean_imo(imo: str) -> str:
    """Normalise IMO to 7-digit string, strip 'IMO' prefix."""
    return re.sub(r"[^\d]", "", str(imo)).lstrip("0").zfill(7)


def _lookup_local_register(imo: str) -> Optional[VesselParams]:
    """Search ships_register.csv by IMO number."""
    if not _SHIPS_REGISTER.exists():
        logger.warning("ships_register.csv not found at %s", _SHIPS_REGISTER)
        return None

    try:
        with open(_SHIPS_REGISTER, newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                row_imo = _clean_imo(row.get("IMO", "0"))
                if row_imo == imo:
                    return _parse_register_row(row)
    except Exception as exc:
        logger.warning("Error reading ships_register: %s", exc)

    return None


def _lookup_local_by_name(name: str) -> Optional[VesselParams]:
    """Name-based search in ships_register.csv (case-insensitive, exact)."""
    if not _SHIPS_REGISTER.exists():
        return None

    name_upper = name.strip().upper()
    try:
        with open(_SHIPS_REGISTER, newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                if row.get("Vessel", "").strip().upper() == name_upper:
                    return _parse_register_row(row)
    except Exception as exc:
        logger.warning("Error in name search: %s", exc)

    return None


def _parse_register_row(row: dict) -> VesselParams:
    """Convert a ships_register CSV row to VesselParams."""
    def _float(v: str) -> Optional[float]:
        try:
            f = float(v)
            return f if f > 0 else None
        except (ValueError, TypeError):
            return None

    def _int(v: str) -> Optional[int]:
        try:
            i = int(float(v))
            return i if i > 0 else None
        except (ValueError, TypeError):
            return None

    draft_m = _float(row.get("Dwt_Draft(m)", ""))
    return VesselParams(
        imo=_clean_imo(row.get("IMO", "0")),
        name=row.get("Vessel", "").strip() or None,
        vessel_type=row.get("Type", "").strip() or None,
        grt=_int(row.get("GT", "")),
        nrt=_int(row.get("NRT", "")),
        dwt=_int(row.get("DWT", "")),
        loa_m=_float(row.get("LOA", "")),
        beam_m=_float(row.get("Beam", "")),
        draft_m=draft_m,
        source="local_register",
        confidence="high",
    )


# ---------------------------------------------------------------------------
# Cache (JSON file — simple, no DuckDB dependency for this module)
# ---------------------------------------------------------------------------

def _load_cache() -> dict:
    if _CACHE_FILE.exists():
        try:
            return json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _write_cache(params: VesselParams) -> None:
    if not params.imo:
        return
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    cache = _load_cache()
    import datetime
    entry = params.to_dict()
    entry["cached_at"] = datetime.datetime.utcnow().isoformat()
    cache[params.imo] = entry
    try:
        _CACHE_FILE.write_text(
            json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except Exception as exc:
        logger.warning("Failed to write vessel cache: %s", exc)


def _lookup_cache(imo: str) -> Optional[VesselParams]:
    cache = _load_cache()
    entry = cache.get(imo)
    if not entry:
        return None
    params = VesselParams(
        imo=entry.get("imo"),
        name=entry.get("name"),
        vessel_type=entry.get("vessel_type"),
        flag=entry.get("flag"),
        grt=entry.get("grt"),
        nrt=entry.get("nrt"),
        dwt=entry.get("dwt"),
        loa_m=entry.get("loa_m"),
        beam_m=entry.get("beam_m"),
        draft_m=entry.get("draft_m"),
        source="cache",
        confidence="medium",
    )
    params.warnings.append(f"Loaded from cache (originally from {entry.get('source', 'unknown')})")
    return params


# ---------------------------------------------------------------------------
# Equasis.org scrape
# ---------------------------------------------------------------------------

def _scrape_equasis(imo: str) -> Optional[VesselParams]:
    """Scrape vessel details from Equasis.org public search.

    Equasis is the European Maritime Safety Agency (EMSA) vessel database.
    Requires free registration; public search form at equasis.org.
    Returns GT, DWT, flag, vessel type, year built.

    Note: Equasis periodically changes their URL structure. If this fails,
    the MarineTraffic fallback will be attempted next.
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        logger.warning("requests/beautifulsoup4 not installed — skipping Equasis scrape")
        return None

    # Equasis public ship search — try both URL patterns
    base = "https://www.equasis.org"
    search_urls = [
        f"{base}/EquasisWeb/public/ShipSearch",
        f"{base}/EquasisWeb/restricted/ShipSearch",
    ]
    payload = {
        "P_IMO": imo,
        "P_SHIPTYP": "",
        "P_NAME": "",
        "P_CALL": "",
        "P_MMSI": "",
        "submit": "Search",
    }

    try:
        session = requests.Session()
        # Establish session / cookies
        home = session.get(
            f"{base}/EquasisWeb/public/HomePage",
            headers=_SCRAPE_HEADERS,
            timeout=_SCRAPE_TIMEOUT,
        )
        time.sleep(0.5)

        for url in search_urls:
            try:
                resp = session.post(
                    url,
                    data=payload,
                    headers=_SCRAPE_HEADERS,
                    timeout=_SCRAPE_TIMEOUT,
                )
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    result = _parse_equasis_response(soup, imo)
                    if result:
                        return result
            except Exception:
                continue

    except Exception as exc:
        logger.warning("Equasis scrape failed for IMO %s: %s", imo, exc)

    return None


def _parse_equasis_response(soup, imo: str) -> Optional[VesselParams]:
    """Parse Equasis HTML response into VesselParams."""
    try:
        # Look for vessel name in result table
        name_tag = soup.find("a", class_="links") or soup.find("td", string=re.compile(r"\w{3,}"))
        vessel_name = name_tag.get_text(strip=True) if name_tag else None

        def _find_value(label: str) -> Optional[str]:
            """Find a table cell value by its label."""
            tag = soup.find(string=re.compile(label, re.I))
            if tag and tag.parent:
                sibling = tag.parent.find_next_sibling("td")
                if sibling:
                    return sibling.get_text(strip=True)
            return None

        def _parse_num(s: Optional[str]) -> Optional[float]:
            if not s:
                return None
            cleaned = re.sub(r"[^\d.]", "", s)
            try:
                return float(cleaned) if cleaned else None
            except ValueError:
                return None

        gt_raw = _find_value(r"Gross\s*Tonnage|GT")
        dwt_raw = _find_value(r"Deadweight|DWT")
        flag_raw = _find_value(r"Flag")
        type_raw = _find_value(r"Ship\s*Type|Type\s*of\s*Ship")

        gt = _parse_num(gt_raw)
        dwt = _parse_num(dwt_raw)

        if not gt and not dwt:
            return None  # Didn't get useful data

        params = VesselParams(
            imo=imo,
            name=vessel_name,
            vessel_type=type_raw,
            flag=flag_raw,
            grt=int(gt) if gt else None,
            dwt=int(dwt) if dwt else None,
            source="equasis",
            source_url=f"https://www.equasis.org (IMO {imo})",
            confidence="high",
        )
        if not params.is_complete:
            params.warnings.append("Draft not available from Equasis — using DWT-based estimate")
            if dwt:
                # Rough draft estimate: bulk carriers ~0.75m per 10,000 DWT (very approximate)
                params.draft_m = round((dwt / 10000) * 0.75 + 4.0, 1)
                params.confidence = "medium"
        return params

    except Exception as exc:
        logger.warning("Error parsing Equasis response: %s", exc)
        return None


# ---------------------------------------------------------------------------
# MarineTraffic.com scrape
# ---------------------------------------------------------------------------

def _scrape_marinetraffic(imo: str) -> Optional[VesselParams]:
    """Scrape vessel details from MarineTraffic public vessel detail page.

    URL pattern: https://www.marinetraffic.com/en/ais/details/ships/imo:{IMO}
    Returns GT, DWT, LOA, beam, flag, vessel type.
    Note: MarineTraffic may rate-limit — uses 1-second delay and respects 429.
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        logger.warning("requests/beautifulsoup4 not installed — skipping MarineTraffic scrape")
        return None

    url = f"https://www.marinetraffic.com/en/ais/details/ships/imo:{imo}"
    time.sleep(1.0)  # Polite delay

    try:
        resp = requests.get(
            url,
            headers=_SCRAPE_HEADERS,
            timeout=_SCRAPE_TIMEOUT,
            allow_redirects=True,
        )

        if resp.status_code == 429:
            logger.warning("MarineTraffic rate limited for IMO %s", imo)
            return None
        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        return _parse_marinetraffic_response(soup, imo, url)

    except Exception as exc:
        logger.warning("MarineTraffic scrape failed for IMO %s: %s", imo, exc)
        return None


def _parse_marinetraffic_response(soup, imo: str, url: str) -> Optional[VesselParams]:
    """Parse MarineTraffic HTML into VesselParams."""
    try:
        def _find_detail(label_pattern: str) -> Optional[str]:
            tag = soup.find(string=re.compile(label_pattern, re.I))
            if tag and tag.parent:
                # Value is typically in a sibling span or next element
                nxt = tag.parent.find_next("span") or tag.parent.find_next("td")
                if nxt:
                    return nxt.get_text(strip=True)
            return None

        def _parse_num(s: Optional[str]) -> Optional[float]:
            if not s:
                return None
            cleaned = re.sub(r"[^\d.]", "", s)
            try:
                return float(cleaned) if cleaned else None
            except ValueError:
                return None

        name_tag = soup.find("h1") or soup.find("title")
        vessel_name = name_tag.get_text(strip=True).split("|")[0].strip() if name_tag else None

        gt = _parse_num(_find_detail(r"Gross\s*Tonnage"))
        dwt = _parse_num(_find_detail(r"Deadweight"))
        loa = _parse_num(_find_detail(r"Length\s*Overall|LOA"))
        beam = _parse_num(_find_detail(r"Breadth\s*Extreme|Beam|Breadth"))
        draft = _parse_num(_find_detail(r"Draft|Draught"))
        flag_raw = _find_detail(r"Flag")
        type_raw = _find_detail(r"Vessel\s*Type|Ship\s*Type")

        if not gt:
            return None

        params = VesselParams(
            imo=imo,
            name=vessel_name,
            vessel_type=type_raw,
            flag=flag_raw,
            grt=int(gt) if gt else None,
            dwt=int(dwt) if dwt else None,
            loa_m=loa,
            beam_m=beam,
            draft_m=draft,
            source="marinetraffic",
            source_url=url,
            confidence="medium",
        )
        params.warnings.append("Source: MarineTraffic — verify against official documents")
        return params

    except Exception as exc:
        logger.warning("Error parsing MarineTraffic response: %s", exc)
        return None
