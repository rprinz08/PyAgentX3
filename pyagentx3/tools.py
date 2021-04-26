# -*- coding: utf-8 -*-

# --------------------------------------------
import logging
class NullHandler(logging.Handler):
    def emit(self, record):
        pass
logger = logging.getLogger('pyagentx3.tools')
logger.addHandler(NullHandler())
# --------------------------------------------

import pyagentx3


FMT = '{}  {}  |{}|'
def hexdump(byte_string, length=16, base_addr=0, n=0, sep='-'):
    not_shown = ['  ']
    leader = (base_addr + n) % length
    next_n = n + length - leader

    while byte_string[n:]:
        col0 = format(n + base_addr - leader, '08x')
        col1 = not_shown * leader
        col2 = ' ' * leader
        leader = 0

        for i in bytearray(byte_string[n:next_n]):
            col1 += [format(i, '02x')]
            col2 += chr(i) if 31 < i < 127 else '.'

        trailer = length - len(col1)
        if trailer:
            col1 += not_shown * trailer
            col2 += ' ' * trailer
        col1.insert(length // 2, sep)

        yield FMT.format(col0, ' '.join(col1), col2)

        n = next_n
        next_n += length
