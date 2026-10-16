"""Real negative-auth checks. Never logs URLs, passwords or raw connection errors."""
import json
import os
from urllib.parse import urlsplit
from uuid import uuid4
import psycopg
from psycopg.conninfo import make_conninfo
from redis import Redis
from redis.exceptions import AuthenticationError


def main():
    database=os.environ.get('DATABASE_URL'); redis_url=os.environ.get('REDIS_URL')
    if not database or not redis_url: raise SystemExit('Database and Redis configuration required')
    with psycopg.connect(database,connect_timeout=3) as conn: conn.execute('SELECT PostGIS_Version()').fetchone()
    try:
        with psycopg.connect(make_conninfo(database,password=uuid4().hex),connect_timeout=3): pass
    except psycopg.OperationalError as error:
        if 'password authentication failed' not in str(error).lower():
            raise SystemExit('Negative database authentication check was inconclusive') from None
    else: raise SystemExit('Database accepted an incorrect password')
    target=urlsplit(redis_url)
    if not target.password: raise SystemExit('Authenticated Redis URL required')
    with Redis.from_url(redis_url,socket_connect_timeout=3,socket_timeout=3) as client: assert client.ping()
    for password in (None,uuid4().hex):
        client=Redis(host=target.hostname,port=target.port or 6379,password=password,
                     ssl=target.scheme=='rediss',socket_connect_timeout=3,socket_timeout=3)
        try:
            try: client.ping()
            except AuthenticationError: pass
            else: raise SystemExit('Redis accepted missing/incorrect authentication')
        finally: client.close()
    print(json.dumps({'postgres_authenticated':True,'postgres_wrong_password_rejected':True,
                      'redis_authenticated':True,'redis_missing_and_wrong_password_rejected':True}))


if __name__=='__main__': main()
