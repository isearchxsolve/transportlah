"""Authenticate the disposable loopback CI Redis before running application checks."""
import os
from urllib.parse import urlsplit
from redis import Redis


if __name__=='__main__':
    target=urlsplit(os.environ['REDIS_URL'])
    if os.getenv('GITHUB_ACTIONS')!='true' or os.getenv('TL_TEST_DATABASE_CONFIRMED')!='1' or target.hostname!='127.0.0.1' or not target.password:
        raise SystemExit('Bootstrap is restricted to acknowledged disposable loopback CI')
    with Redis(host=target.hostname,port=target.port or 6379,socket_timeout=3) as client:
        client.config_set('requirepass',target.password)
    print('Disposable CI Redis authentication configured')
