from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..db.session import get_db

router = APIRouter(prefix="/api/v1/stats", tags=["stats"])


def _stats_params(
    tech: str | None,
    method: str | None,
    operator_id: int | None,
    region_code: str | None,
    dept_code: str | None,
) -> dict:
    return {
        "tech": tech,
        "method": method,
        "operator_id": operator_id,
        "region_code": region_code,
        "dept_code": dept_code,
    }


@router.get("/summary")
def get_summary(
    tech: str | None = Query(default=None),
    method: str | None = Query(default=None),
    operator_id: int | None = Query(default=None),
    region_code: str | None = Query(default=None),
    dept_code: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = text(
        """
        WITH point_weights AS (
            SELECT
                sc.method,
                sc.tech,
                sc.operator_id,
                sc.is_covered,
                rs.road_type,
                rs.region_code,
                rs.dept_code,
                COALESCE(rs.length_m, 0)
                    / NULLIF(COUNT(*) OVER (PARTITION BY sc.method, sc.tech, sc.operator_id, rsp.segment_id), 0)
                    AS represented_length_m
            FROM ter.sample_coverage sc
            JOIN ter.road_sample_point rsp ON rsp.id = sc.sample_point_id
            JOIN ter.road_segment rs ON rs.id = rsp.segment_id
            WHERE (CAST(:tech AS text) IS NULL OR sc.tech = CAST(:tech AS text))
              AND (CAST(:method AS text) IS NULL OR sc.method = CAST(:method AS text))
              AND (CAST(:operator_id AS integer) IS NULL OR sc.operator_id = CAST(:operator_id AS integer))
              AND (CAST(:region_code AS text) IS NULL OR rs.region_code = CAST(:region_code AS text))
              AND (CAST(:dept_code AS text) IS NULL OR rs.dept_code = CAST(:dept_code AS text))
        ),
        grouped AS (
            SELECT
                method,
                tech,
                operator_id,
                is_covered,
                road_type,
                region_code,
                dept_code,
                COUNT(*)::int AS nb_points,
                SUM(represented_length_m) AS length_m
            FROM point_weights
            GROUP BY method, tech, operator_id, is_covered, road_type, region_code, dept_code
        )
        SELECT
            method,
            tech,
            operator_id,
            is_covered,
            road_type,
            region_code,
            dept_code,
            nb_points,
            ROUND((length_m / 1000.0)::numeric, 3)::float AS length_km,
            CASE
                WHEN SUM(length_m) OVER (PARTITION BY method, tech, operator_id, road_type, region_code, dept_code) > 0
                THEN ROUND(
                    (length_m / SUM(length_m) OVER (PARTITION BY method, tech, operator_id, road_type, region_code, dept_code))::numeric,
                    4
                )::float
                ELSE 0
            END AS coverage_ratio
        FROM grouped
        ORDER BY method, tech, operator_id, road_type, region_code, dept_code, is_covered;
        """
    )
    rows = db.execute(query, _stats_params(tech, method, operator_id, region_code, dept_code)).mappings().all()
    return {"items": [dict(r) for r in rows]}


@router.get("/compare")
def compare_methods(
    tech: str | None = Query(default=None),
    operator_id: int | None = Query(default=None),
    region_code: str | None = Query(default=None),
    dept_code: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = text(
        """
        WITH point_weights AS (
            SELECT
                sc.method,
                sc.tech,
                sc.operator_id,
                o.name AS operator_name,
                sc.is_covered,
                COALESCE(rs.length_m, 0)
                    / NULLIF(COUNT(*) OVER (PARTITION BY sc.method, sc.tech, sc.operator_id, rsp.segment_id), 0)
                    AS represented_length_m
            FROM ter.sample_coverage sc
            JOIN ter.ref_operator o ON o.id = sc.operator_id
            JOIN ter.road_sample_point rsp ON rsp.id = sc.sample_point_id
            JOIN ter.road_segment rs ON rs.id = rsp.segment_id
            WHERE (CAST(:tech AS text) IS NULL OR sc.tech = CAST(:tech AS text))
              AND (CAST(:operator_id AS integer) IS NULL OR sc.operator_id = CAST(:operator_id AS integer))
              AND (CAST(:region_code AS text) IS NULL OR rs.region_code = CAST(:region_code AS text))
              AND (CAST(:dept_code AS text) IS NULL OR rs.dept_code = CAST(:dept_code AS text))
        ),
        method_stats AS (
            SELECT
                tech,
                operator_id,
                operator_name,
                method,
                SUM(CASE WHEN is_covered THEN represented_length_m ELSE 0 END) AS covered_m,
                SUM(represented_length_m) AS total_m
            FROM point_weights
            GROUP BY tech, operator_id, operator_name, method
        )
        SELECT
            tech,
            operator_id,
            operator_name,
            ROUND((SUM(CASE WHEN method = 'A_THEORETICAL' THEN covered_m ELSE 0 END) / 1000.0)::numeric, 3)::float AS a_covered_km,
            ROUND((SUM(CASE WHEN method = 'B_OFFICIAL' THEN covered_m ELSE 0 END) / 1000.0)::numeric, 3)::float AS b_covered_km,
            CASE
                WHEN SUM(CASE WHEN method = 'A_THEORETICAL' THEN total_m ELSE 0 END) > 0
                THEN ROUND((
                    SUM(CASE WHEN method = 'A_THEORETICAL' THEN covered_m ELSE 0 END)
                    / SUM(CASE WHEN method = 'A_THEORETICAL' THEN total_m ELSE 0 END)
                )::numeric, 4)::float
                ELSE 0
            END AS a_ratio,
            CASE
                WHEN SUM(CASE WHEN method = 'B_OFFICIAL' THEN total_m ELSE 0 END) > 0
                THEN ROUND((
                    SUM(CASE WHEN method = 'B_OFFICIAL' THEN covered_m ELSE 0 END)
                    / SUM(CASE WHEN method = 'B_OFFICIAL' THEN total_m ELSE 0 END)
                )::numeric, 4)::float
                ELSE 0
            END AS b_ratio
        FROM method_stats
        GROUP BY tech, operator_id, operator_name
        ORDER BY tech, operator_name;
        """
    )
    rows = db.execute(query, _stats_params(tech, None, operator_id, region_code, dept_code)).mappings().all()
    return {"items": [dict(r) for r in rows]}
