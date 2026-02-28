"""
Pydantic models for cargo and tonnage data.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class LinkTonnage(BaseModel):
    """Link tonnage (cargo volumes) model."""

    model_config = ConfigDict(from_attributes=True)

    objectid: int = Field(..., description="Unique object identifier")
    linknum: int = Field(..., description="Link number (foreign key to waterway_links)")

    # Total tonnages
    totalup: int = Field(default=0, ge=0, description="Total tonnage upstream")
    totaldown: int = Field(default=0, ge=0, description="Total tonnage downstream")

    # Coal
    coalup: int = Field(default=0, ge=0, description="Coal tonnage upstream")
    coaldown: int = Field(default=0, ge=0, description="Coal tonnage downstream")

    # Petroleum
    petrolup: int = Field(default=0, ge=0, description="Petroleum tonnage upstream")
    petrodown: int = Field(default=0, ge=0, description="Petroleum tonnage downstream")

    # Chemicals
    chemup: int = Field(default=0, ge=0, description="Chemical tonnage upstream")
    chemdown: int = Field(default=0, ge=0, description="Chemical tonnage downstream")

    # Crude materials
    crmatup: int = Field(default=0, ge=0, description="Crude materials upstream")
    crmatdown: int = Field(default=0, ge=0, description="Crude materials downstream")

    # Manufactured goods
    manuup: int = Field(default=0, ge=0, description="Manufactured goods upstream")
    manudown: int = Field(default=0, ge=0, description="Manufactured goods downstream")

    # Farm products
    farmup: int = Field(default=0, ge=0, description="Farm products upstream")
    farmdown: int = Field(default=0, ge=0, description="Farm products downstream")

    # Machinery
    machup: int = Field(default=0, ge=0, description="Machinery upstream")
    machdown: int = Field(default=0, ge=0, description="Machinery downstream")

    # Waste
    wasteup: int = Field(default=0, ge=0, description="Waste upstream")
    wastedown: int = Field(default=0, ge=0, description="Waste downstream")

    # Unknown
    unkwnup: int = Field(default=0, ge=0, description="Unknown cargo upstream")
    unkwdown: int = Field(default=0, ge=0, description="Unknown cargo downstream")

    shape_length: Optional[float] = Field(None, ge=0)

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def total_tonnage(self) -> int:
        """Calculate total tonnage (both directions)."""
        return self.totalup + self.totaldown

    @property
    def net_flow(self) -> int:
        """Calculate net flow (positive = more downstream, negative = more upstream)."""
        return self.totaldown - self.totalup

    @property
    def primary_commodity(self) -> str:
        """Determine the primary commodity by volume."""
        commodities = {
            'coal': self.coalup + self.coaldown,
            'petroleum': self.petrolup + self.petrodown,
            'chemicals': self.chemup + self.chemdown,
            'crude_materials': self.crmatup + self.crmatdown,
            'manufactured': self.manuup + self.manudown,
            'farm': self.farmup + self.farmdown,
            'machinery': self.machup + self.machdown,
            'waste': self.wasteup + self.wastedown,
        }

        if not any(commodities.values()):
            return 'none'

        return max(commodities.items(), key=lambda x: x[1])[0]

    def get_commodity_breakdown(self) -> dict[str, int]:
        """Get breakdown of all commodities with totals."""
        return {
            'coal': self.coalup + self.coaldown,
            'petroleum': self.petrolup + self.petrodown,
            'chemicals': self.chemup + self.chemdown,
            'crude_materials': self.crmatup + self.crmatdown,
            'manufactured': self.manuup + self.manudown,
            'farm': self.farmup + self.farmdown,
            'machinery': self.machup + self.machdown,
            'waste': self.wasteup + self.wastedown,
            'unknown': self.unkwnup + self.unkwdown,
        }


class CommodityType(BaseModel):
    """Commodity type definition for cargo classification."""

    name: str = Field(..., max_length=50)
    description: Optional[str] = None
    hazmat: bool = Field(default=False, description="Hazardous materials indicator")
    density_kg_m3: Optional[float] = Field(None, ge=0, description="Typical density")
    value_per_ton_usd: Optional[float] = Field(None, ge=0, description="Approximate value per ton")


# Standard commodity definitions
COMMODITY_TYPES = {
    'coal': CommodityType(
        name='Coal',
        description='Coal and coal products',
        hazmat=False,
        density_kg_m3=800,
        value_per_ton_usd=50
    ),
    'petroleum': CommodityType(
        name='Petroleum',
        description='Crude oil and petroleum products',
        hazmat=True,
        density_kg_m3=850,
        value_per_ton_usd=500
    ),
    'chemicals': CommodityType(
        name='Chemicals',
        description='Chemical products',
        hazmat=True,
        density_kg_m3=1000,
        value_per_ton_usd=1000
    ),
    'crude_materials': CommodityType(
        name='Crude Materials',
        description='Raw materials and ores',
        hazmat=False,
        density_kg_m3=1500,
        value_per_ton_usd=30
    ),
    'manufactured': CommodityType(
        name='Manufactured Goods',
        description='Finished manufactured products',
        hazmat=False,
        density_kg_m3=500,
        value_per_ton_usd=2000
    ),
    'farm': CommodityType(
        name='Farm Products',
        description='Agricultural products and grains',
        hazmat=False,
        density_kg_m3=600,
        value_per_ton_usd=200
    ),
    'machinery': CommodityType(
        name='Machinery',
        description='Heavy machinery and equipment',
        hazmat=False,
        density_kg_m3=2000,
        value_per_ton_usd=5000
    ),
    'waste': CommodityType(
        name='Waste',
        description='Waste materials',
        hazmat=True,
        density_kg_m3=1000,
        value_per_ton_usd=0
    ),
}
