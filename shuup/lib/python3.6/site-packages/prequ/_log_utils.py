from __future__ import absolute_import

import logging
from contextlib import contextmanager


class LogCollector(logging.Handler):
    def __init__(self):
        self.records = []
        super(LogCollector, self).__init__()

    def handle(self, record):
        self.records.append(record)

    def get_messages(self):
        return [x.getMessage() for x in self.records]


@contextmanager
def collect_logs():
    collector = LogCollector()
    logging.root.addHandler(collector)
    old_level = logging.root.level
    logging.root.setLevel(logging.DEBUG)
    try:
        yield collector
    finally:
        logging.root.removeHandler(collector)
        logging.root.setLevel(old_level)
