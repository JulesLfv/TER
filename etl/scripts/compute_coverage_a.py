import argparse
from sqlalchemy import create_engine, text
from config import settings
from filters import bbox_params, bbox_sql, parse_bbox


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bbox", default=None, help="Optional EPSG:4326 bbox: minx,miny,maxx,maxy")
    parser.add_argument("--append", action="store_true", help="Append instead of replacing A_THEORETICAL rows")
    args = parser.parse_args()
    bbox = parse_bbox(args.bbox)
    where_sql = f"WHERE {bbox_sql('p.geom')}" if bbox else ""

    engine = create_engine(settings.database_url)
    sql = text(
        f"""
        INSERT INTO ter.sample_coverage
            (sample_point_id, method, tech, operator_id, is_covered, nearest_site_id, distance_to_site_m)
        SELECT p.id,
               'A_THEORETICAL',
               s.tech,
               s.operator_id,
               CASE
                 WHEN s.tech='4G' AND d.dist_m <= :r4g THEN TRUE
                 WHEN s.tech='5G' AND d.dist_m <= :r5g THEN TRUE
                 ELSE FALSE
               END AS is_covered,
               s.id,
               d.dist_m
        FROM ter.road_sample_point p
        JOIN LATERAL (
            SELECT rs.id, rs.tech, rs.operator_id,
                   ST_Distance(ST_Transform(p.geom, 2154), ST_Transform(rs.geom, 2154)) AS dist_m
            FROM ter.radio_site rs
            ORDER BY p.geom <-> rs.geom
            LIMIT 1
        ) d ON TRUE
        JOIN ter.radio_site s ON s.id = d.id
        {where_sql}
        ;
        """
    )
    with engine.begin() as conn:
        if not args.append:
            conn.execute(text("DELETE FROM ter.sample_coverage WHERE method = 'A_THEORETICAL'"))
        conn.execute(sql, {"r4g": settings.radius_4g_m, "r5g": settings.radius_5g_m, **bbox_params(bbox)})


if __name__ == "__main__":
    main()
