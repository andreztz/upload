import sys
from twisted.web.client import Agent
from twisted.python import log
from twisted.web.http_headers import Headers
from twisted.internet.defer import succeed, inlineCallbacks, Deferred
from twisted.internet.task import react, LoopingCall
from twisted.web.client import FileBodyProducer


class SlowProducer(object):
    def __init__(self, data, repeat=3, delay=1):
        self._data = [data] * repeat
        self.length = len(data) * repeat
        self.senders = []
        self.delay = delay
        self.sender = LoopingCall(self._doSend)
        self.consumer = None
        self.finished = Deferred()

    def startProducing(self, consumer):
        if self.consumer is not None:
            raise ValueError('Consumer already set')
        self.consumer = consumer
        self.sender.start(self.delay, now=False)
        log.msg('start sending: %d bytes total' % (self.length, ))
        return self.finished

    def _doSend(self):
        if not self._data:
            self.stopProducing()
        part = self._data.pop()
        log.msg('sent %d bytes' % (len(part), ))
        self.consumer.write(part)

    def pauseProducing(self):
        self.sender.pause()

    def stopProducing(self):
        log.msg('finished sending')
        self.sender.stop()
        self.finished.callback(None)


@inlineCallbacks
def main(reactor):
    agent = Agent(reactor)
    body = SlowProducer("hello world")
    yield agent.request('POST', 'http://localhost:8080', Headers(), body)



if __name__ == '__main__':
    log.startLogging(sys.stdout)
    react(main)