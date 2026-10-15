"""Generated TEST_VECTOR catalog cases, never real DataMall captures."""
from copy import deepcopy
from datetime import datetime,timezone
import unittest
import httpx
from backend.app.catalog import CatalogFetcher, DATASETS, normalize_catalog
from backend.app.transport import SourceUnavailable, raw_hash


def catalog_vector():
    now=datetime.now(timezone.utc).isoformat()
    stops=[{'BusStopCode':'00001','RoadName':'TEST_VECTOR','Description':'A','Latitude':1.3,'Longitude':103.8},
           {'BusStopCode':'00002','RoadName':'TEST_VECTOR','Description':'B','Latitude':1.31,'Longitude':103.81}]
    services=[{'ServiceNo':'T1','Operator':'TEST','Direction':1},{'ServiceNo':'T1','Operator':'TEST','Direction':2}]
    routes=[]
    for direction,codes in ((1,['00001','00002','00001']),(2,['00002','00001'])):
        for sequence,code in enumerate(codes,1):
            routes.append({'ServiceNo':'T1','Operator':'TEST','Direction':direction,'StopSequence':sequence,
                           'BusStopCode':code,'Distance':(sequence-1)*1.5,'WD_FirstBus':'0530','WD_LastBus':'2359'})
    pages=[]
    for dataset,rows in zip(DATASETS,(stops,services,routes)):
        raw={'value':rows}
        pages.append({'dataset':dataset,'skip':0,'captured_at_utc':now,'raw_sha256':raw_hash(raw),'raw':raw})
    return {'provenance':'TEST_VECTOR','started_at_utc':now,'completed_at_utc':now,'pages':pages}


def rehash(document):
    for page in document['pages']: page['raw_sha256']=raw_hash(page['raw'])
    return document


class CatalogChecks(unittest.TestCase):
    def test_direction_and_repeated_stop_occurrences_remain_distinct(self):
        result=normalize_catalog(catalog_vector())
        self.assertEqual(len(result['services']),2)
        self.assertEqual([r['BusStopCode'] for r in result['routes'][('T1','TEST',1)]],['00001','00002','00001'])
        self.assertEqual(len(result['version']),64)

    def test_tampered_raw_capture_and_missing_provenance_are_rejected(self):
        document=catalog_vector(); document['pages'][0]['raw']['value'][0]['Latitude']=1.4
        with self.assertRaises(ValueError): normalize_catalog(document)
        document=catalog_vector(); document['provenance']='OFFLINE_FAKE'
        with self.assertRaises(ValueError): normalize_catalog(document)

    def test_missing_terminal_dataset_out_of_order_and_duplicate_pages_fail(self):
        for mutate in (lambda d:d['pages'].pop(),lambda d:d['pages'][0].update(skip=500),
                       lambda d:d['pages'].append(deepcopy(d['pages'][0]))):
            document=catalog_vector(); mutate(document)
            with self.assertRaises(ValueError): normalize_catalog(document)

    def test_unknown_stops_missing_services_sequence_gaps_and_backwards_distance_fail(self):
        changes=({'BusStopCode':'99999'},{'ServiceNo':'NO'},{'StopSequence':9},{'Distance':-1})
        for change in changes:
            document=catalog_vector(); document['pages'][2]['raw']['value'][1].update(change)
            with self.subTest(change=change),self.assertRaises(ValueError): normalize_catalog(rehash(document))

    def test_duplicate_stop_and_service_records_fail_even_when_identical(self):
        for index in (0,1):
            document=catalog_vector(); rows=document['pages'][index]['raw']['value']; rows.append(deepcopy(rows[0]))
            with self.assertRaises(ValueError): normalize_catalog(rehash(document))

    def test_nonfinite_zero_and_bad_range_coordinates_fail(self):
        for lat,lon in ((float('nan'),103.8),(0,0),(91,103.8),(True,103.8),(1.3,181)):
            document=catalog_vector(); document['pages'][0]['raw']['value'][0].update(Latitude=lat,Longitude=lon)
            with self.assertRaises(ValueError): normalize_catalog(rehash(document))

    def test_capture_window_and_timezone_are_required(self):
        for value in ('2026-10-15T00:00:00','2000-01-01T00:00:00+00:00'):
            document=catalog_vector(); document['pages'][0]['captured_at_utc']=value
            with self.assertRaises(ValueError): normalize_catalog(document)


class CatalogTransportChecks(unittest.IsolatedAsyncioTestCase):
    async def test_actual_pagination_parameters_do_not_follow_untrusted_next_links(self):
        vector=catalog_vector(); requests=[]
        # Fill the first page with500 unique generated stops to force the second request.
        rows=[{**vector['pages'][0]['raw']['value'][0],'BusStopCode':f'{i:05}'} for i in range(1,501)]
        def handler(request):
            requests.append((request.url.path,int(request.url.params['$skip'])))
            dataset=request.url.path.rsplit('/',1)[1]; offset=int(request.url.params['$skip'])
            if dataset=='BusStops': payload=rows if offset==0 else []
            else: payload=next(p['raw']['value'] for p in vector['pages'] if p['dataset']==dataset)
            return httpx.Response(200,json={'value':payload,'@odata.nextLink':'https://attacker.example/steal-key'})
        fetcher=CatalogFetcher('TEST_VECTOR:operator-key',client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),provenance='TEST_VECTOR')
        try: document=await fetcher.capture()
        finally: await fetcher.close()
        self.assertEqual([offset for _,offset in requests],[0,500,0,0])
        self.assertEqual(len(normalize_catalog(document)['stops']),500)
        self.assertEqual(document['provenance'],'TEST_VECTOR')

    async def test_upstream_denial_malformed_and_oversize_responses_fail_without_fallback(self):
        for response in (httpx.Response(429),httpx.Response(200,json={'value':'bad'}),httpx.Response(200,content=b'x'*(2*1024*1024+1))):
            fetcher=CatalogFetcher('TEST_VECTOR:key',provenance='TEST_VECTOR',client=httpx.AsyncClient(transport=httpx.MockTransport(lambda r:response)))
            try:
                with self.assertRaises(SourceUnavailable): await fetcher.capture()
            finally: await fetcher.close()

    async def test_repeated_full_page_and_page_limit_fail(self):
        rows=[{**catalog_vector()['pages'][0]['raw']['value'][0],'BusStopCode':f'{i:05}'} for i in range(1,501)]
        for max_pages in (1,2):
            fetcher=CatalogFetcher('TEST_VECTOR:key',provenance='TEST_VECTOR',max_pages=max_pages,
                                   client=httpx.AsyncClient(transport=httpx.MockTransport(lambda r:httpx.Response(200,json={'value':rows}))))
            try:
                with self.assertRaises(SourceUnavailable): await fetcher.capture()
            finally: await fetcher.close()

    def test_no_key_is_an_explicit_error(self):
        with self.assertRaises(ValueError): CatalogFetcher('')
