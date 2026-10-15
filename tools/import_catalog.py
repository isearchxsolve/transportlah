"""Capture official catalog or import a preserved capture; never generate a fallback."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import sys
import psycopg
from dotenv import load_dotenv

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.app.catalog import CatalogFetcher, import_catalog, normalize_catalog
from backend.app.transport import SourceUnavailable


async def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--capture',type=Path,help='Existing preserved catalog document')
    parser.add_argument('--write-database',action='store_true')
    args=parser.parse_args(); load_dotenv(ROOT/'.env')
    if args.capture:
        document=json.loads(args.capture.read_text(encoding='utf-8'))
        result=normalize_catalog(document)
    else:
        key=os.getenv('LTA_DATAMALL_KEY','').strip()
        if not key and os.getenv('LTA_KEY_PATH'): key=Path(os.environ['LTA_KEY_PATH']).read_text(encoding='utf-8').strip()
        if not key: raise SystemExit('LTA key is not configured; no catalog capture/import executed')
        fetcher=CatalogFetcher(key)
        try: document=await fetcher.capture()
        finally: await fetcher.close()
        result=normalize_catalog(document)
        folder=ROOT/'private/catalog'; folder.mkdir(parents=True,exist_ok=True)
        # Exclusive creation preserves an existing capture; successful DB retry can reuse it.
        path=folder/(result['version']+'.json')
        with path.open('x',encoding='utf-8') as output: json.dump(document,output,indent=2,allow_nan=False)
    if args.write_database:
        url=os.getenv('MIGRATION_DATABASE_URL')
        if not url: raise SystemExit('MIGRATION_DATABASE_URL is required; no database import executed')
        with psycopg.connect(url) as conn: import_catalog(conn,document)
    print(json.dumps({'version':result['version'],'provenance':document['provenance'],'stops':len(result['stops']),
                      'service_directions':len(result['services']),'route_occurrences':sum(len(r) for r in result['routes'].values()),
                      'database_imported':args.write_database,'active_catalog_promoted':False}))


if __name__=='__main__':
    try: asyncio.run(main())
    except (SourceUnavailable,ValueError,KeyError,psycopg.Error):
        raise SystemExit('Catalog capture/validation/import failed; existing versions remain unchanged') from None
