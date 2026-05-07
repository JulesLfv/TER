def parse_bbox(value: str | None) -> tuple[float, float, float, float] | None:
    if not value:
        return None
    parts = [float(part.strip()) for part in value.split(",")]
    if len(parts) != 4:
        raise ValueError("bbox must be minx,miny,maxx,maxy in EPSG:4326")
    return parts[0], parts[1], parts[2], parts[3]


def bbox_sql(alias: str = "geom") -> str:
    return f"ST_Intersects({alias}, ST_MakeEnvelope(:minx, :miny, :maxx, :maxy, 4326))"


def bbox_params(bbox: tuple[float, float, float, float] | None) -> dict:
    if not bbox:
        return {}
    return {"minx": bbox[0], "miny": bbox[1], "maxx": bbox[2], "maxy": bbox[3]}
