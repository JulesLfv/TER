from typing import Optional, Literal
from pydantic import BaseModel, Field


Tech = Literal["4G", "5G"]
Method = Literal["A_THEORETICAL", "B_OFFICIAL"]


class GeoFilter(BaseModel):
    bbox: Optional[str] = Field(default=None, description="minx,miny,maxx,maxy in EPSG:4326")
    tech: Optional[Tech] = None
    operator_id: Optional[int] = None
    road_type: Optional[str] = None
    region_code: Optional[str] = None
    dept_code: Optional[str] = None
    method: Optional[Method] = None
    limit: int = Field(default=5000, ge=1, le=50000)

    def bbox_tuple(self) -> Optional[tuple[float, float, float, float]]:
        if not self.bbox:
            return None
        vals = [float(v.strip()) for v in self.bbox.split(",")]
        if len(vals) != 4:
            raise ValueError("bbox must contain 4 comma-separated values")
        return vals[0], vals[1], vals[2], vals[3]
