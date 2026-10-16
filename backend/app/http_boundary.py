"""ASGI body bound; checks chunks without retaining oversized request bodies."""
from starlette.responses import JSONResponse


class BoundedBodyMiddleware:
    def __init__(self,app,maximum=262144): self.app=app; self.maximum=maximum

    async def __call__(self,scope,receive,send):
        if scope['type']!='http': return await self.app(scope,receive,send)
        lengths=[v for k,v in scope['headers'] if k.lower()==b'content-length']
        status=None
        if lengths and (len(lengths)!=1 or not lengths[0].isdigit()): status=400
        elif lengths and int(lengths[0])>self.maximum: status=413
        if status:
            return await JSONResponse({'detail':'Invalid or oversized request body'},status_code=status)(scope,receive,send)
        body=bytearray()
        while True:
            message=await receive()
            if message['type']=='http.disconnect': return
            if message['type']!='http.request': continue
            chunk=message.get('body',b'')
            if len(body)+len(chunk)>self.maximum:
                return await JSONResponse({'detail':'Request body exceeds capacity'},status_code=413)(scope,receive,send)
            body.extend(chunk)
            if not message.get('more_body',False): break
        sent=False
        async def replay():
            nonlocal sent
            if not sent:
                sent=True
                return {'type':'http.request','body':bytes(body),'more_body':False}
            return await receive()
        await self.app(scope,replay,send)
