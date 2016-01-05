from multipart import MultipartParser
import tornado.ioloop
import tornado.web

class FormDataReceiver(object):
    def __init__(self, boundary, **kwargs):
        print 'xd', repr(boundary)
        self.parser = MultipartParser(boundary, {
            'on_part_begin': self.on_part_begin,
            'on_part_data': self.on_part_data,
            'on_part_end': self.on_part_end,
        })

    def data_received(self, data):
        self.parser.write(data)

    def finish(self):
        pass

    def on_part_begin(self):
        pass

    def on_part_data(self, data, start, end):
        print 'data', repr(data[start:end]), start, end

    def on_part_end(self):
        pass



class DumpingReceiver(object):
    pass

def parse_content_type(header):
    parts = header.lower().split(';')
    content_type, opts = parts[0], parts[1:]
    options = {k.strip(): v.strip()
        for k, sep, v in
        (option.partition('=') for option in opts)
    }
    return content_type, options

@tornado.web.stream_request_body
class MainHandler(tornado.web.RequestHandler):
    def initialize(self):
        print 'init'

    def data_received(self, data):
        self.receiver.data_received(data)

    def prepare(self):
        content_type_header = self.request.headers.get('content-type')
        content_type, opts = parse_content_type(content_type_header)
        receiver_class = {
            'multipart/form-data': FormDataReceiver,
        }.get(content_type, DumpingReceiver)
        self.receiver = receiver_class(**opts)

    def post(self):
        self.receiver.finish()
        print 'posting'
        self.write("Hello, world")

if __name__ == "__main__":
    application = tornado.web.Application([
        (r"/", MainHandler),
    ])
    application.listen(8080)
    tornado.ioloop.IOLoop.current().start()
