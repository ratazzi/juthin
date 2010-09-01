from cStringIO import StringIO
from tornado.httpclient import HTTPRequest, HTTPResponse, HTTPError
from tornado.httputil import HTTPHeaders
from tornado.ioloop import IOLoop
from tornado.iostream import IOStream
from tornado import stack_context

import functools
import logging
import re
import socket
import urlparse

class SimpleAsyncHTTPClient(object):
    # TODO: singleton magic?
    def __init__(self, io_loop=None):
        self.io_loop = io_loop or IOLoop.instance()

    def close(self):
        pass

    def fetch(self, request, callback, **kwargs):
        if not isinstance(request, HTTPRequest):
            request = HTTPRequest(url=request, **kwargs)
        callback = stack_context.wrap(callback)

        parsed = urlparse.urlsplit(request.url)
        sock = socket.socket()
        #sock.setblocking(False) # TODO non-blocking connect
        sock.connect((parsed.netloc, 80))  # TODO: other ports, https
        stream = IOStream(sock, io_loop=self.io_loop)
        # TODO: query parameters
        logging.warning("%s %s HTTP/1.0\r\n\r\n" % (request.method, parsed.path or '/'))
        stream.write("%s %s HTTP/1.0\r\n\r\n" % (request.method, parsed.path or '/'))
        stream.read_until("\r\n\r\n", functools.partial(self._on_headers,
                                                        request, callback, stream))

    def _on_headers(self, request, callback, stream, data):
        logging.warning(data)
        first_line, _, header_data = data.partition("\r\n")
        match = re.match("HTTP/1.[01] ([0-9]+) .*", first_line)
        assert match
        code = int(match.group(1))
        headers = HTTPHeaders.parse(header_data)
        assert "Content-Length" in headers
        stream.read_bytes(int(headers["Content-Length"]),
                          functools.partial(self._on_body, request, callback, stream, code, headers))

    def _on_body(self, request, callback, stream, code, headers, data):
        response = HTTPResponse(request, code, headers=headers,
                                buffer=StringIO(data)) # TODO
        callback(response)

def main():
    from tornado.options import define, options, parse_command_line
    args = parse_command_line()
    client = SimpleAsyncHTTPClient()
    io_loop = IOLoop.instance()
    for arg in args:
        def callback(response):
            response.rethrow()
            print response.body
            io_loop.stop()
        client.fetch(arg, callback)
        io_loop.start()

if __name__ == "__main__":
    main()
