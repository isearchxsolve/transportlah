"""Deterministic catalog-backed evidence checks; not passenger presence proof."""
from decimal import Decimal
import math
import re
from .verification import Observation,State


def _outcome(state,reason):
    return Observation(state,Decimal(1) if state==State.PASSED else Decimal(0),reason)


def _catalog(conn,version,allow_test):
    if type(allow_test) is not bool or not isinstance(version,str) or not re.fullmatch('[a-f0-9]{64}',version):
        raise ValueError('Invalid catalog version/test policy')
    row=conn.execute('SELECT provenance FROM tl.catalog_versions WHERE id=%s',(version,)).fetchone()
    return row is not None and (row[0]=='LIVE_NETWORK' or allow_test)


def boarding_proximity(conn,*,version,stop_code,latitude,longitude,accuracy_metres,radius_metres=50,max_accuracy_metres=50,allow_test=False):
    values=(latitude,longitude,accuracy_metres,radius_metres,max_accuracy_metres)
    if any(type(v) not in (int,float) or not math.isfinite(v) for v in values): raise ValueError('Finite typed measurements required')
    if not (-90<=latitude<=90 and -180<=longitude<=180 and 0<accuracy_metres<10000 and 0<radius_metres<=2000 and 0<max_accuracy_metres<=1000):
        raise ValueError('Invalid measurement/tolerance')
    if not isinstance(stop_code,str) or not re.fullmatch('[0-9]{5}',stop_code): raise ValueError('Invalid stop')
    if not _catalog(conn,version,allow_test): return _outcome(State.UNAVAILABLE,'catalog_unavailable_or_test_only')
    if accuracy_metres>max_accuracy_metres: return _outcome(State.UNAVAILABLE,'device_accuracy_insufficient')
    row=conn.execute('SELECT ST_Distance(location,ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography) FROM tl.catalog_stops WHERE version=%s AND code=%s',
                     (longitude,latitude,version,stop_code)).fetchone()
    if not row: return _outcome(State.UNAVAILABLE,'boarding_stop_not_in_catalog')
    distance=row[0]
    if distance+accuracy_metres<=radius_metres: return _outcome(State.PASSED,'accuracy_envelope_inside_boarding_radius')
    if distance-accuracy_metres>radius_metres: return _outcome(State.FAILED,'accuracy_envelope_outside_boarding_radius')
    return _outcome(State.UNAVAILABLE,'boarding_accuracy_boundary_ambiguous')


def service_sequence(conn,*,version,service,operator,direction,boarding_sequence,alighting_sequence,boarding_stop,alighting_stop,allow_test=False):
    if (not isinstance(service,str) or not re.fullmatch('[A-Za-z0-9]{1,8}',service) or
        not isinstance(operator,str) or not re.fullmatch('[A-Za-z0-9]{1,16}',operator) or
        type(direction) is not int or direction not in (1,2) or
        any(type(n) is not int or n<1 for n in (boarding_sequence,alighting_sequence)) or
        any(not isinstance(s,str) or not re.fullmatch('[0-9]{5}',s) for s in (boarding_stop,alighting_stop))):
        raise ValueError('Invalid service/direction/occurrences')
    if not _catalog(conn,version,allow_test): return _outcome(State.UNAVAILABLE,'catalog_unavailable_or_test_only')
    rows=conn.execute('SELECT sequence,stop_code FROM tl.catalog_route_stops WHERE version=%s AND service=%s AND operator=%s AND direction=%s AND sequence=ANY(%s)',
                      (version,service,operator,direction,[boarding_sequence,alighting_sequence])).fetchall()
    occurrences=dict(rows)
    if alighting_sequence<=boarding_sequence: return _outcome(State.FAILED,'alighting_not_downstream')
    if occurrences.get(boarding_sequence)!=boarding_stop or occurrences.get(alighting_sequence)!=alighting_stop:
        return _outcome(State.FAILED,'selected_service_direction_or_stop_occurrence_contradicted')
    return _outcome(State.PASSED,'catalog_service_direction_and_downstream_occurrences_match')
