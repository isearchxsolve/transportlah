"""Apply immutable versioned migrations with a privileged, tool-only connection."""
import hashlib
import os
from pathlib import Path
import psycopg


def migrate(url):
    with psycopg.connect(url) as conn:
        conn.execute("SELECT pg_advisory_xact_lock(817426901)")
        conn.execute("CREATE EXTENSION IF NOT EXISTS postgis")
        conn.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
        conn.execute("CREATE TABLE IF NOT EXISTS public.tl_schema_versions (version text PRIMARY KEY, sha256 text NOT NULL)")
        for path in sorted((Path(__file__).resolve().parents[1]/'backend/migrations').glob('*.sql')):
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            row=conn.execute("SELECT sha256 FROM public.tl_schema_versions WHERE version=%s",(path.name,)).fetchone()
            if row:
                if row[0]!=digest:
                    raise RuntimeError("Applied migration has changed: "+path.name)
                continue
            conn.execute(path.read_text(encoding='utf-8'))
            conn.execute("INSERT INTO public.tl_schema_versions VALUES (%s,%s)",(path.name,digest))


if __name__=='__main__':
    url=os.getenv('MIGRATION_DATABASE_URL')
    if not url:
        raise SystemExit('MIGRATION_DATABASE_URL is required; no migration executed')
    migrate(url)
    print('Versioned migrations verified/applied')
