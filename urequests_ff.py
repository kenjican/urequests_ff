#import usocket
from uasyncio import core # Kenji

class Stream:
    def __init__(self, s, e={}):
        self.s = s
        self.e = e
        self.out_buf = b""

    def get_extra_info(self, v):
        return self.e[v]

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    def close(self):
        pass

    async def wait_closed(self):
        # TODO yield?
        self.s.close()

    async def read(self, n):
        yield core._io_queue.queue_read(self.s)
        return self.s.read(n)

    async def readinto(self, buf):
        yield core._io_queue.queue_read(self.s)
        return self.s.readinto(buf)

    async def readexactly(self, n):
        r = b""
        while n:
            yield core._io_queue.queue_read(self.s)
            r2 = self.s.read(n)
            if r2 is not None:
                if not len(r2):
                    raise EOFError
                r += r2
                n -= len(r2)
        return r

    async def readline(self):
        l = b""
        while True:
            yield core._io_queue.queue_read(self.s)
            l2 = self.s.readline()  # may do multiple reads but won't block
            l += l2
            if not l2 or l[-1] == 10:  # \n (check l in case l2 is str)
                return l

    def write(self, buf):
        self.out_buf += buf

    async def drain(self):
        mv = memoryview(self.out_buf)
        off = 0
        while off < len(mv):
            yield core._io_queue.queue_write(self.s)
            ret = self.s.write(mv[off:])
            if ret is not None:
                off += ret
        self.out_buf = b""



class Response:
    def __init__(self, f):
        self.raw = f
        self.encoding = "utf-8"
        self._cached = None

    def close(self):
        if self.raw:
            self.raw.wait_closed()
            self.raw = None
        self._cached = None

    @property
    def content(self):
        if self._cached is None:
            try:
                self._cached = self.raw.read()
            finally:
                self.raw.wait_closed()
                self.raw = None
        return self._cached

    @property
    def text(self):
        return str(self.content, self.encoding)

    def json(self):
        import ujson

        return ujson.loads(self.content)


async def request(method, url, data=None, json=None, headers={}, stream=None):
    #from uerrno import EINPROGRESS
    import usocket
    try:
        proto, dummy, host, path = url.split("/", 3)
    except ValueError:
        proto, dummy, host = url.split("/", 2)
        path = ""
    if proto == "http:":
        port = 80
    elif proto == "https:":
        import ussl

        port = 443
    else:
        raise ValueError("Unsupported protocol: " + proto)

    if ":" in host:
        host, port = host.split(":", 1)
        port = int(port)

    ai = usocket.getaddrinfo(host, port, 0, usocket.SOCK_STREAM)
    ai = ai[0]
    #print(ai[-1])
    s = usocket.socket(ai[0], ai[1], ai[2])
    #s.setblocking(False)#Kenji
    #ss = Stream(s)
    try:
        s.connect(ai[-1])
        if proto == "https:":
            s = ussl.wrap_socket(s, server_hostname=host)
        #print("wrap ussl")
        s.setblocking(False)
        yield core._io_queue.queue_write(s)
        ss = Stream(s)
        ss.write(b"%s /%s HTTP/1.0\r\n" % (method, path))
        if not "Host" in headers:
            ss.write(b"Host: %s\r\n" % host)
        # Iterate over keys to avoid tuple alloc
        for k in headers:
            ss.write(k)
            ss.write(b": ")
            ss.write(headers[k])
            ss.write(b"\r\n")
        if json is not None:
            assert data is None
            import ujson

            data = ujson.dumps(json)
            ss.write(b"Content-Type: application/json\r\n")
        if data:
            ss.write(b"Content-Length: %d\r\n" % len(data))
        ss.write(b"\r\n")
        if data:
            ss.write(data)
            await ss.drain()
        l = await ss.readline()
        #print(l)
        l = l.split(None, 2)
        status = int(l[1])
        reason = ""
        if len(l) > 2:
            reason = l[2].rstrip()
        while True:
            l = await ss.readline()
            #print(l)
            if not l or l == b"\r\n":
                break
            # print(l)
            if l.startswith(b"Transfer-Encoding:"):
                if b"chunked" in l:
                    raise ValueError("Unsupported " + l)
            elif l.startswith(b"Location:") and not 200 <= status <= 299:
                raise NotImplementedError("Redirects not yet supported")
    except OSError:
        ss.close()
        raise

    resp = Response(ss)
    resp.status_code = status
    resp.reason = reason
    return resp


def head(url, **kw):
    return request("HEAD", url, **kw)


def get(url, **kw):
    return request("GET", url, **kw)


def post(url, **kw):
    return request("POST", url, **kw)


def put(url, **kw):
    return request("PUT", url, **kw)


def patch(url, **kw):
    return request("PATCH", url, **kw)


def delete(url, **kw):
    return request("DELETE", url, **kw)
