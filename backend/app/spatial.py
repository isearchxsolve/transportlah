"""Metre-correct queries. Route matching is context, never proof of boarding."""
import math

CORRIDOR_SQL = """
SELECT id, ST_Distance(path, ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography) AS distance_metres
FROM tl.route_patterns
WHERE mode = %s AND geometry_quality = 'authoritative'
AND ST_DWithin(path, ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography, %s)
"""

POSITION_SQL = """
SELECT id FROM tl.arrival_observations
WHERE position_observed_at IS NOT NULL
AND position_observed_at BETWEEN %s::timestamptz - interval '30 seconds'
                             AND %s::timestamptz + interval '30 seconds'
AND ST_DWithin(position, ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography, %s)
"""


def haversine_metres(lat1, lon1, lat2, lon2, *, radius=6371008.7714150598):
    """Spherical reference for differential tests, not ellipsoidal production distance."""
    values = (lat1, lon1, lat2, lon2, radius)
    if any(type(v) not in {int, float} or not math.isfinite(v) for v in values):
        raise ValueError("Coordinates/radius must be finite numbers")
    if not (-90 <= lat1 <= 90 and -90 <= lat2 <= 90 and -180 <= lon1 <= 180
            and -180 <= lon2 <= 180 and radius > 0):
        raise ValueError("Coordinates/radius out of range")
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2-p1)/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(math.radians(lon2-lon1)/2)**2
    return 2*radius*math.atan2(math.sqrt(min(1,a)), math.sqrt(max(0,1-a)))
