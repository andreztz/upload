from cgi import FieldStorage
import sys

from twisted.internet.task import react
from twisted.internet.defer import Deferred

from twisted.internet.endpoints import serverFromString
from twisted.web.resource import Resource
from twisted.web.server import Site


class UploadResource(Resource):
    def getChild(self, path, request):
        if not path:
            return self
        return Resource.getChild(path, request)

    def render_GET(self, request):
        return """
        <!doctype html>
        <html>
        <head>
            <title>upload</title>
        </head>
        <body>
            <form action="" method="POST" enctype="multipart/form-data">
                <input type="file" name="upfile" />
                <input type="submit" />
            </form>
        </body>
        </html>
        """

    def render_POST(self, request):
        print request.args
        fs = FieldStorage(request.content)
        print dict(fs)
        return 'asd'

def main(reactor):
    ep = serverFromString(reactor, 'tcp:8080')
    f = Site(UploadResource())
    ep.listen(f)
    return Deferred()

if __name__ == '__main__':
    react(main)
