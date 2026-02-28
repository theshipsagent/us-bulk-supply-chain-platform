"""
Pydantic models for vessel data.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class Vessel(BaseModel):
    """Vessel registry model."""

    model_config = ConfigDict(from_attributes=True)

    imo: str = Field(..., max_length=20, description="IMO number (unique identifier)")
    vessel_name: Optional[str] = Field(None, max_length=255)
    design: Optional[str] = Field(None, max_length=100, description="Vessel design type")
    vessel_type: Optional[str] = Field(None, max_length=100, description="Vessel type classification")

    # Tonnage
    dwt: Optional[int] = Field(None, ge=0, description="Deadweight tonnage")
    gt: Optional[int] = Field(None, ge=0, description="Gross tonnage")
    nrt: Optional[int] = Field(None, ge=0, description="Net registered tonnage")
    grain: Optional[int] = Field(None, ge=0, description="Grain capacity")

    # Dimensions (critical for routing constraints)
    loa: Optional[float] = Field(None, ge=0, description="Length overall in meters")
    beam: Optional[float] = Field(None, ge=0, description="Beam width in meters (critical for locks)")
    depth_m: Optional[float] = Field(None, ge=0, description="Draft depth in meters (critical for channels)")

    # Additional specs
    tpc: Optional[float] = Field(None, description="Tonnes per centimeter immersion")
    dwt_draft_m: Optional[float] = Field(None, ge=0, description="Draft at DWT in meters")
    source_file: Optional[str] = Field(None, max_length=255)

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def has_dimensions(self) -> bool:
        """Check if vessel has complete dimensional data."""
        return self.beam is not None and self.depth_m is not None and self.loa is not None

    def can_pass_lock(self, lock_width_feet: Optional[float], lock_length_feet: Optional[float],
                      safety_margin_m: float = 0.5) -> bool:
        """
        Check if vessel can pass through a lock.

        Args:
            lock_width_feet: Lock chamber width in feet
            lock_length_feet: Lock chamber length in feet
            safety_margin_m: Required clearance margin in meters

        Returns:
            True if vessel can pass, False otherwise
        """
        if not self.has_dimensions:
            return False

        if lock_width_feet is None or lock_length_feet is None:
            return False

        # Convert lock dimensions from feet to meters
        lock_width_m = lock_width_feet * 0.3048
        lock_length_m = lock_length_feet * 0.3048

        # Check width constraint
        width_ok = self.beam <= (lock_width_m - safety_margin_m)

        # Check length constraint
        length_ok = self.loa <= (lock_length_m - safety_margin_m)

        return width_ok and length_ok

    def can_navigate_channel(self, channel_depth_m: Optional[float],
                            safety_margin_m: float = 1.5) -> bool:
        """
        Check if vessel can safely navigate a channel.

        Args:
            channel_depth_m: Channel depth in meters
            safety_margin_m: Required under-keel clearance (default 1.5m)

        Returns:
            True if vessel can navigate, False otherwise
        """
        if self.depth_m is None or channel_depth_m is None:
            return False

        # Vessel draft + safety margin must not exceed channel depth
        return (self.depth_m + safety_margin_m) <= channel_depth_m

    def get_clearance_requirements(self) -> dict[str, float]:
        """
        Get vessel's clearance requirements.

        Returns:
            Dictionary with required clearances
        """
        return {
            'min_lock_width_m': (self.beam + 0.5) if self.beam else 0,
            'min_lock_length_m': (self.loa + 0.5) if self.loa else 0,
            'min_channel_depth_m': (self.depth_m + 1.5) if self.depth_m else 0,
            'beam_m': self.beam or 0,
            'length_m': self.loa or 0,
            'draft_m': self.depth_m or 0,
        }


class VesselType(BaseModel):
    """Vessel type classification."""

    name: str = Field(..., max_length=100)
    category: str = Field(..., max_length=50, description="General category (barge, tanker, etc.)")
    typical_cargo: Optional[list[str]] = Field(default_factory=list)
    avg_beam_m: Optional[float] = Field(None, ge=0)
    avg_length_m: Optional[float] = Field(None, ge=0)
    avg_draft_m: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None


# Common vessel types for inland waterways
VESSEL_TYPES = {
    'dry_bulk_barge': VesselType(
        name='Dry Bulk Barge',
        category='barge',
        typical_cargo=['coal', 'grain', 'aggregates'],
        avg_beam_m=10.7,  # ~35 feet
        avg_length_m=59.4,  # ~195 feet
        avg_draft_m=2.7,  # ~9 feet loaded
        description='Standard hopper barge for dry bulk cargo'
    ),
    'tank_barge': VesselType(
        name='Tank Barge',
        category='barge',
        typical_cargo=['petroleum', 'chemicals'],
        avg_beam_m=10.7,
        avg_length_m=59.4,
        avg_draft_m=2.7,
        description='Tank barge for liquid cargo'
    ),
    'jumbo_hopper': VesselType(
        name='Jumbo Hopper Barge',
        category='barge',
        typical_cargo=['coal', 'grain'],
        avg_beam_m=16.5,  # ~54 feet
        avg_length_m=91.4,  # ~300 feet
        avg_draft_m=3.7,  # ~12 feet loaded
        description='Large capacity hopper barge'
    ),
    'towboat': VesselType(
        name='Towboat',
        category='tow',
        typical_cargo=[],
        avg_beam_m=12.2,
        avg_length_m=30.5,
        avg_draft_m=2.4,
        description='Inland river towboat'
    ),
}
