"""Bounded DataMall catalog capture and immutable, versioned normalization."""
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
import re
from uuid import NAMESPACE_URL, uuid5

import httpx
from psycopg.types.json import Jsonb
from .transport import SourceUnavailable, raw_hash, MAX_RESPONSE_BYTES


DATASETS=('BusStops','BusServices','BusRoutes')
BASE_URL='https://datamall2.mytransport.sg/ltaodataservice/'
PAGE_SIZE=500
MAX_CATALOG_BYTES=64*1024*1024


class CatalogFetcher:
    def __init__(self,key,*,client=None,provenance='LIVE_NETWORK',max_pages=500):
        if not key: raise ValueError('An LTA key is required; no catalog fallback')
        if provenance not in {'LIVE_NETWORK','TEST_VECTOR'} or type(max_pages) is not int or not 1<=max_pages<=500:
            raise ValueError('Invalid catalog provenance/capacity')
        self.key=key; self.provenance=provenance; self.max_pages=max_pages
        self.client=client or httpx.AsyncClient(timeout=10,follow_redirects=False)

    async def close(self): await self.client.aclose()

    async def capture(self):
        pages=[]; total_bytes=0; started=datetime.now(timezone.utc)
        try:
            for dataset in DATASETS:
                seen=set()
                for index in range(self.max_pages):
                    async with self.client.stream('GET',BASE_URL+dataset,params={'$skip':index*PAGE_SIZE},
                                                 headers={'AccountKey':self.key,'accept':'application/json'}) as response:
                        if response.status_code!=200:
                            raise SourceUnavailable('Catalog upstream rejected the request',status_code=502)
                        content=bytearray()
                        async for chunk in response.aiter_bytes():
                            content.extend(chunk); total_bytes+=len(chunk)
                            if len(content)>MAX_RESPONSE_BYTES or total_bytes>MAX_CATALOG_BYTES:
                                raise SourceUnavailable('Catalog response exceeds capacity',status_code=502)
                    raw=json.loads(content)
                    rows=raw.get('value') if isinstance(raw,dict) else None
                    if not isinstance(rows,list) or len(rows)>PAGE_SIZE or any(not isinstance(r,dict) for r in rows):
                        raise SourceUnavailable('Catalog page structure is invalid',status_code=502)
                    digest=raw_hash(raw)
                    if rows and digest in seen: raise SourceUnavailable('Repeated catalog page; pagination did not advance',status_code=502)
                    seen.add(digest)
                    pages.append({'dataset':dataset,'skip':index*PAGE_SIZE,'captured_at_utc':datetime.now(timezone.utc).isoformat(),
                                  'raw_sha256':digest,'raw':raw})
                    if len(rows)<PAGE_SIZE: break
                else:
                    raise SourceUnavailable('Catalog pagination exhausted the configured limit',status_code=502)
        except (httpx.HTTPError,ValueError,UnicodeDecodeError):
            raise SourceUnavailable('Catalog network/decoding failure',status_code=502) from None
        document={'provenance':self.provenance,'started_at_utc':started.isoformat(),
                  'completed_at_utc':datetime.now(timezone.utc).isoformat(),'pages':pages}
        normalize_catalog(document)  # Reject inconsistent captures before persistence.
        return document


def catalog_version(document):
    return hashlib.sha256(json.dumps(document,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def _time(value):
    parsed=datetime.fromisoformat(value)
    if parsed.tzinfo is None: raise ValueError('Catalog timestamp needs a timezone')
    return parsed


def _string(row,key,pattern):
    value=row.get(key)
    if not isinstance(value,str) or not re.fullmatch(pattern,value): raise ValueError('Invalid catalog '+key)
    return value


def _integer(row,key):
    value=row.get(key)
    if type(value) is not int or value<1: raise ValueError('Invalid catalog '+key)
    return value


def normalize_catalog(document):
    if not isinstance(document,dict) or document.get('provenance') not in {'LIVE_NETWORK','TEST_VECTOR'}:
        raise ValueError('Catalog provenance is mandatory')
    started=_time(document['started_at_utc']); completed=_time(document['completed_at_utc'])
    if completed<started or (completed-started).total_seconds()>900:
        raise ValueError('Catalog capture window invalid or too long')
    pages=document.get('pages')
    if not isinstance(pages,list) or not 3<=len(pages)<=1500: raise ValueError('Catalog page bounds invalid')
    datasets={name:[] for name in DATASETS}; terminal=set(); offsets={name:0 for name in DATASETS}
    hashes={name:set() for name in DATASETS}; size=0
    for page in pages:
        if not isinstance(page,dict): raise ValueError('Invalid catalog page')
        name=page.get('dataset'); raw=page.get('raw')
        if name not in datasets or name in terminal or type(page.get('skip')) is not int or page['skip']!=offsets[name]:
            raise ValueError('Catalog page order/scope invalid')
        captured=_time(page['captured_at_utc'])
        if not started<=captured<=completed: raise ValueError('Page capture time outside collection window')
        if not isinstance(raw,dict) or raw_hash(raw)!=page['raw_sha256']: raise ValueError('Catalog payload integrity failed')
        rows=raw.get('value')
        if not isinstance(rows,list) or len(rows)>PAGE_SIZE or any(not isinstance(r,dict) for r in rows):
            raise ValueError('Invalid catalog rows')
        encoded=json.dumps(raw,allow_nan=False).encode(); size+=len(encoded)
        if len(encoded)>MAX_RESPONSE_BYTES or size>MAX_CATALOG_BYTES: raise ValueError('Catalog payload too large')
        if rows and page['raw_sha256'] in hashes[name]: raise ValueError('Repeated catalog page')
        hashes[name].add(page['raw_sha256']); datasets[name].extend(rows); offsets[name]+=PAGE_SIZE
        if len(rows)<PAGE_SIZE: terminal.add(name)
    if terminal!=set(DATASETS) or any(not datasets[n] for n in DATASETS): raise ValueError('Incomplete/empty catalog')
    stops={}; services={}; routes=defaultdict(dict)
    for row in datasets['BusStops']:
        code=_string(row,'BusStopCode',r'[0-9]{5}')
        lat=row.get('Latitude'); lon=row.get('Longitude')
        if any(type(v) not in (int,float) or not math.isfinite(v) for v in (lat,lon)) or not (-90<=lat<=90 and -180<=lon<=180) or (lat,lon)==(0,0):
            raise ValueError('Invalid/unavailable stop coordinates')
        if code in stops: raise ValueError('Duplicate stop across catalog pages')
        stops[code]=row
    for row in datasets['BusServices']:
        key=(_string(row,'ServiceNo',r'[A-Za-z0-9]{1,8}'),_string(row,'Operator',r'[A-Za-z0-9]{1,16}'),_integer(row,'Direction'))
        if key[2] not in (1,2) or key in services: raise ValueError('Duplicate/invalid service direction')
        services[key]=row
    for row in datasets['BusRoutes']:
        key=(_string(row,'ServiceNo',r'[A-Za-z0-9]{1,8}'),_string(row,'Operator',r'[A-Za-z0-9]{1,16}'),_integer(row,'Direction'))
        seq=_integer(row,'StopSequence'); code=_string(row,'BusStopCode',r'[0-9]{5}')
        if key not in services or code not in stops or seq in routes[key]: raise ValueError('Route references missing/duplicate catalog evidence')
        try: distance=Decimal(str(row['Distance']))
        except (InvalidOperation,KeyError): raise ValueError('Invalid route distance') from None
        if not distance.is_finite() or distance<0: raise ValueError('Invalid route distance')
        routes[key][seq]=row
    for key,occurrences in routes.items():
        ordered=[occurrences[n] for n in sorted(occurrences)]
        if sorted(occurrences)!=list(range(1,len(ordered)+1)): raise ValueError('Route stop sequence has gaps')
        distances=[Decimal(str(r['Distance'])) for r in ordered]
        if distances!=sorted(distances): raise ValueError('Route cumulative distance moves backwards')
        routes[key]=ordered
    if set(routes)!=set(services): raise ValueError('A catalog service direction has no route records')
    return {'version':catalog_version(document),'stops':stops,'services':services,'routes':dict(routes)}


def import_catalog(conn,document):
    """Privileged tool only. One transaction; no live promotion from test data."""
    normalized=normalize_catalog(document); version=normalized['version']
    with conn.transaction():
        conn.execute('SELECT pg_advisory_xact_lock(817426902)')
        if conn.execute('SELECT 1 FROM tl.catalog_versions WHERE id=%s',(version,)).fetchone(): return version
        conn.execute('INSERT INTO tl.catalog_versions VALUES (%s,%s,%s,%s,%s)',
                     (version,document['provenance'],document['started_at_utc'],document['completed_at_utc'],Jsonb(document)))
        for code,row in normalized['stops'].items():
            conn.execute('INSERT INTO tl.catalog_stops VALUES (%s,%s,%s,%s,ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography)',
                         (version,code,row.get('RoadName',''),row.get('Description',''),row['Longitude'],row['Latitude']))
        for key,row in normalized['services'].items():
            conn.execute('INSERT INTO tl.catalog_services VALUES (%s,%s,%s,%s,%s)',(version,*key,Jsonb(row)))
        for key,rows in normalized['routes'].items():
            route_id=uuid5(NAMESPACE_URL,'transportlah:'+version+':'+':'.join(map(str,key)))
            coords=[normalized['stops'][r['BusStopCode']] for r in rows]
            # Single-stop or entirely coincident routes have no usable line; preserve raw route records anyway.
            has_path=len({(r['Longitude'],r['Latitude']) for r in coords})>=2
            if has_path:
                wkt='LINESTRING('+','.join(f"{r['Longitude']} {r['Latitude']}" for r in coords)+')'
                conn.execute("INSERT INTO tl.route_patterns VALUES (%s,'bus',%s,%s,%s,%s,ST_GeogFromText(%s))",
                             (route_id,key[0],str(key[2]),version,'TEST_VECTOR' if document['provenance']=='TEST_VECTOR' else 'stop_sequence_chord',wkt))
            for row in rows:
                conn.execute('INSERT INTO tl.catalog_route_stops VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                             (version,*key,row['StopSequence'],row['BusStopCode'],Decimal(str(row['Distance'])),route_id if has_path else None,Jsonb(row)))
        # Active catalog promotion is a separate privileged operation after live consistency review.
    return version
