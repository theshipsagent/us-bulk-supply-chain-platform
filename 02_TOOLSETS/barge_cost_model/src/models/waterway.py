"""
Pydantic models for waterway network data.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class WaterwayLink(BaseModel):
    """Waterway network link/segment model."""

    model_config = ConfigDict(from_attributes=True)

    objectid: int = Field(..., description="Unique object identifier")
    id: Optional[int] = Field(None, description="Secondary identifier")
    length_miles: Optional[float] = Field(None, ge=0, description="Length in miles")
    dir: Optional[int] = Field(None, description="Direction indicator")
    linknum: int = Field(..., description="Link number (join key)")
    anode: int = Field(..., description="Start node for routing")
    bnode: int = Field(..., description="End node for routing")
    linkname: Optional[str] = Field(None, max_length=255, description="Link name")
    rivername: Optional[str] = Field(None, max_length=255, description="River name")
    amile: Optional[float] = Field(None, description="A-node mile marker")
    bmile: Optional[float] = Field(None, description="B-node mile marker")
    length1: Optional[float] = Field(None, description="Alternative length measurement")
    length_src: Optional[str] = Field(None, description="Length data source")
    shape_src: Optional[str] = Field(None, description="Shape data source")
    linktype: Optional[str] = Field(None, description="Type of waterway link")
    waterway: Optional[str] = Field(None, description="Waterway identifier")
    geo_class: Optional[str] = Field(None, description="Geographic classification")
    func_class: Optional[str] = Field(None, description="Functional classification")
    wtwy_type: Optional[str] = Field(None, description="Waterway type")
    chart_id: Optional[str] = Field(None, description="Chart identifier")
    num_pairs: Optional[int] = Field(None, description="Number of pairs")
    who_mod: Optional[str] = Field(None, description="Last modifier")
    date_mod: Optional[str] = Field(None, description="Last modification date")
    heading: Optional[str] = Field(None, description="Heading/direction")
    state: Optional[str] = Field(None, max_length=2, description="State code")
    fips: Optional[str] = Field(None, description="FIPS code")
    fips2: Optional[str] = Field(None, description="Secondary FIPS code")
    non_us: Optional[str] = Field(None, description="Non-US indicator")
    key_id: Optional[str] = Field(None, description="Key identifier")
    waterway_unique: Optional[str] = Field(None, description="Unique waterway ID")
    min_meas: Optional[float] = Field(None, description="Minimum measure")
    max_meas: Optional[float] = Field(None, description="Maximum measure")
    shape_length: Optional[float] = Field(None, ge=0, description="Shape length")

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class WaterwayNode(BaseModel):
    """Waterway network node model."""

    model_config = ConfigDict(from_attributes=True)

    node_id: int = Field(..., description="Node identifier")
    x: Optional[float] = Field(None, description="Longitude")
    y: Optional[float] = Field(None, description="Latitude")
    node_type: Optional[str] = Field(None, description="Type of node")
    connected_links: Optional[list[int]] = Field(default_factory=list, description="Connected link numbers")


class Lock(BaseModel):
    """Lock facility model."""

    model_config = ConfigDict(from_attributes=True)

    objectid: int = Field(..., description="Unique object identifier")
    id: Optional[int] = None
    ndccode: Optional[str] = Field(None, max_length=50)
    region: Optional[str] = Field(None, max_length=10)
    rivercd: Optional[str] = Field(None, max_length=10)
    lockcd: Optional[str] = Field(None, max_length=10)
    chmbcd: Optional[str] = Field(None, max_length=10)
    nochmb: Optional[int] = Field(None, description="Number of chambers")
    pmsdata: Optional[str] = Field(None, max_length=5)
    navstr: Optional[str] = Field(None, max_length=100)
    chambn: Optional[str] = Field(None, max_length=50)
    chb1: Optional[str] = Field(None, max_length=10)
    str1: Optional[str] = Field(None, max_length=10)
    pmsname: Optional[str] = Field(None, max_length=100, description="Lock name")
    status: Optional[str] = Field(None, max_length=50)
    river: Optional[str] = Field(None, max_length=100)
    rivermi: Optional[float] = Field(None, description="River mile")
    bank: Optional[str] = Field(None, max_length=10)
    lift: Optional[float] = Field(None, ge=0, description="Lift height in feet")
    length: Optional[float] = Field(None, ge=0, description="Chamber length in feet")
    chmbul: Optional[float] = Field(None, ge=0, description="Chamber usable length")
    width: Optional[float] = Field(None, ge=0, description="Chamber width in feet (critical constraint)")
    chmbuw: Optional[float] = Field(None, ge=0, description="Chamber usable width")
    audpa: Optional[float] = Field(None, description="Authorized depth point A")
    audpb: Optional[float] = Field(None, description="Authorized depth point B")
    updpthms: Optional[float] = Field(None, description="Upper pool depth")
    lwdpthms: Optional[float] = Field(None, description="Lower pool depth")
    yearopen: Optional[int] = Field(None, ge=1800, le=2100)
    gatetype: Optional[str] = Field(None, max_length=50)
    gate: Optional[str] = Field(None, max_length=50)
    chnlgth: Optional[float] = Field(None, description="Channel length")
    chndptha: Optional[float] = Field(None, description="Channel depth A")
    chndpthb: Optional[float] = Field(None, description="Channel depth B")
    chnwdtha: Optional[float] = Field(None, description="Channel width A")
    chnwdthb: Optional[float] = Field(None, description="Channel width B")
    wwprjct: Optional[str] = Field(None, max_length=100)
    mooring: Optional[str] = Field(None, max_length=10)
    multi: Optional[str] = Field(None, max_length=10)
    division: Optional[str] = Field(None, max_length=50)
    district: Optional[str] = Field(None, max_length=50)
    state: Optional[str] = Field(None, max_length=2)
    maint1: Optional[str] = Field(None, max_length=50)
    oper1: Optional[str] = Field(None, max_length=50)
    owner1: Optional[str] = Field(None, max_length=50)
    town: Optional[str] = Field(None, max_length=100)
    county1: Optional[str] = Field(None, max_length=100)
    mooring_r: Optional[str] = Field(None, max_length=50)
    x: Optional[float] = Field(None, description="Longitude")
    y: Optional[float] = Field(None, description="Latitude")

    # Operational data (populated later)
    avg_wait_time_minutes: Optional[int] = Field(None, ge=0)

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def is_passable_by_vessel(self, vessel_beam_m: float) -> bool:
        """
        Check if a vessel can pass through this lock.

        Args:
            vessel_beam_m: Vessel beam width in meters

        Returns:
            True if vessel can pass, False otherwise
        """
        if not self.width:
            return False  # Unknown width, assume not passable

        # Convert lock width from feet to meters
        lock_width_m = self.width * 0.3048

        # Add safety margin (0.5m clearance)
        return vessel_beam_m <= (lock_width_m - 0.5)


class Dock(BaseModel):
    """Navigation facility/dock model."""

    model_config = ConfigDict(from_attributes=True)

    objectid: int = Field(..., description="Unique object identifier")
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    loc_dock: Optional[str] = Field(None, max_length=50)
    nav_unit_id: Optional[str] = Field(None, max_length=50)
    nav_unit_guid: Optional[str] = Field(None, max_length=50)
    unlocode: Optional[str] = Field(None, max_length=50)
    nav_unit_name: Optional[str] = Field(None, max_length=255, description="Facility name")
    fac_type: Optional[str] = Field(None, max_length=100, description="Facility type")
    data_record_status: Optional[str] = Field(None, max_length=50)
    location_description: Optional[str] = None
    street_address: Optional[str] = Field(None, max_length=255)
    city_or_town: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=2)
    zipcode: Optional[str] = Field(None, max_length=20)
    county_name: Optional[str] = Field(None, max_length=100)
    county_fips_code: Optional[str] = Field(None, max_length=10)
    congress: Optional[str] = Field(None, max_length=50)
    congress_fips: Optional[str] = Field(None, max_length=10)
    tows_link_num: Optional[int] = Field(None, description="Links to waterway network")
    tows_mile: Optional[float] = Field(None)
    wtwy: Optional[str] = Field(None, max_length=50)
    wtwy_name: Optional[str] = Field(None, max_length=255)
    port: Optional[str] = Field(None, max_length=50)
    port_name: Optional[str] = Field(None, max_length=255)
    psa: Optional[str] = Field(None, max_length=50)
    psa_name: Optional[str] = Field(None, max_length=255)
    mile: Optional[float] = Field(None)
    bank: Optional[str] = Field(None, max_length=10)
    operators: Optional[str] = None
    owners: Optional[str] = None
    purpose: Optional[str] = None
    highway_note: Optional[str] = None
    railway_note: Optional[str] = None
    commodities: Optional[str] = None
    construction: Optional[str] = None
    mechanical_handling: Optional[str] = None
    remarks: Optional[str] = None
    vertical_datum: Optional[str] = Field(None, max_length=50)
    depth_min: Optional[float] = Field(None, ge=0, description="Minimum depth (critical for vessel draft)")
    depth_max: Optional[float] = Field(None, ge=0)
    berthing_largest: Optional[float] = Field(None, ge=0)
    berthing_total: Optional[float] = Field(None, ge=0)
    deck_height_min: Optional[float] = Field(None)
    deck_height_max: Optional[float] = Field(None)
    parent_or_child: Optional[str] = Field(None, max_length=50)
    service_initiation_date: Optional[str] = Field(None, max_length=50)
    x: Optional[float] = Field(None, description="Longitude")
    y: Optional[float] = Field(None, description="Latitude")

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def can_accommodate_vessel(self, vessel_draft_m: float, safety_margin_m: float = 1.5) -> bool:
        """
        Check if this dock can accommodate a vessel with given draft.

        Args:
            vessel_draft_m: Vessel draft in meters
            safety_margin_m: Required safety margin (default 1.5m)

        Returns:
            True if dock can accommodate vessel, False otherwise
        """
        if not self.depth_min:
            return False  # Unknown depth, assume not safe

        # Convert depth from feet to meters
        depth_min_m = self.depth_min * 0.3048

        # Check if depth is sufficient with safety margin
        return depth_min_m >= (vessel_draft_m + safety_margin_m)
