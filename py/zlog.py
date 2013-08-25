#!/usr/bin/env python

''' USAGE:
      zlog [<config>] (lol|fyi|wtf|omg) <sender> (-|<message> <message>...)

    <sender> is a logical name of emitting party.

    If <message> is -, message lines are read from stdin.
'''

__all__ = ('ZLogger', 'zlogger')
from socket import gethostname
from zero import *

class ZLogger(object):
    def __init__(self, config, logq, sender, host):
        self.logq = logq
        self.sender = sender
        self.host = host
        for lvl, _ in config['levels']:
            def logout(msg, lvl=lvl):
                self.log(msg, lvl)
            setattr(self, lvl, logout)
    def log(self, msg, level):
        self.logq.put(self.format(self.sender, level, msg, self.host))
    @classmethod
    def format(cls, sender, level, msg, host, ts_format='%Y-%m-%dT%H:%M:%S%Z'):
        from json import dumps
        from time import strftime
        return dumps([sender, host, level, strftime(ts_format), msg])

def zlogger(config, sender):
    from Queue import Queue
    from threading import Thread
    logq = Queue()
    slog = ZeroSetup('push', 'tcp://%(host)s:%(port)s' % config, iter(logq.get, '')).nonblocking()
    def thread(slog=slog):
        for t in zero(slog):
            pass
    t = Thread(target=thread)
    t.daemon = True
    t.start()
    return ZLogger(config, logq, sender, gethostname())
                     
def main():
    from env import HERE
    from sys import argv, exit
    from json import load
    from os.path import exists
    from itertools import imap
    from collections import deque
    from zero import zero, ZeroSetup
    args = deque(argv[1:])
    if len(args) < 3:
        exit(__doc__)
    conf = HERE + '/log.json'
    level = args.popleft()
    if exists(level):
        conf = level
        level = args.popleft()
    with open(conf) as fin:
        conf = load(fin)['log']
    sender = args.popleft()
    if args[0] == '-':
        messages = ZeroSetup.iter_stdin()
    else:
        messages = iter(args)
    messages = imap(lambda x:log_format(conf, sender, level, x), messages)
    z = zero(ZeroSetup('push', conf['port'], messages))
    for msg in z:
        pass

if __name__ == '__main__':
    main()