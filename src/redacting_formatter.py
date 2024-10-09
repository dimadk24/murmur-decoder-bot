import urllib.parse
from logging import Formatter


class RedactingFormatter(Formatter):
    def __init__(self, fmt=None, datefmt=None, style='%', patterns=None):
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)

        self.patterns = []
        for pattern in patterns:
            self.patterns.append(pattern)
            self.patterns.append(urllib.parse.quote_plus(pattern))

    def format(self, record):
        msg = super().format(record)
        for pattern in self.patterns:
            msg = msg.replace(pattern, "[--redacted--]")
        return msg

    def __getattr__(self, attr):
        return getattr(self.orig_formatter, attr)
