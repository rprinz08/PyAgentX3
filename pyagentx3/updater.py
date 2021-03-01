# -*- coding: utf-8 -*-

# --------------------------------------------
import logging
class NullHandler(logging.Handler):
    def emit(self, record):
        pass
logger = logging.getLogger('pyagentx3.updater')
logger.addHandler(NullHandler())
# --------------------------------------------

import time
import threading
from queue import Full
from collections import OrderedDict
import pyagentx3


class Updater(threading.Thread):

    def __init__(self, data_store=None):
        threading.Thread.__init__(self)
        self.data_store = data_store
        self.stop = None
        self._queue = None
        self._oid = None
        self._freq = None
        self._data = None
        self._traps = None

    def agent_setup(self, queue, oid, freq):
        self.stop = threading.Event()
        self._queue = queue
        self._oid = oid
        self._freq = freq
        self._data = {}
        self._traps = {}

    def run(self):
        start_time = 0
        while True:
            if self.stop.is_set():
                break
            now = time.time()
            if now - start_time > self._freq:
                logger.info('Updating : %s (%s)', self.__class__.__name__, self._oid)
                start_time = now
                self._data = {}
                try:
                    self.update()
                    self._queue.put_nowait({'oid': self._oid,
                                            'data': self._data})
                except Full:
                    logger.error('Queue full')
                except Exception as e:
                    logger.exception('Unhandled update exception')
            time.sleep(0.1)
        logger.info('Updater stopping')

    # Override this
    def update(self):
        pass

    def send_trap(self, trap_oid, *values):
        logger.info('Send Trap : %s (%s)', self.__class__.__name__, trap_oid)
        logger.info('Send Trap : %s', values)

        data = OrderedDict()
        # SNMPv2-MIB::snmpTrapOID.0 = trap_oid
        data['1.3.6.1.6.3.1.1.4.1.0'] = self._OBJECTIDENTIFIER('1.3.6.1.6.3.1.1.4.1.0', trap_oid)
        for value in values:
            data[value['name']] = value
        try:
            self._queue.put_nowait({'trap_oid': trap_oid, 'data': data})
        except Full:
            logger.error('Queue full')
        except Exception as e:
            logger.exception('Unhandled trap exception')

    def set_INTEGER(self, oid, value):
        logger.debug('Setting INTEGER %s = %s', oid, value)
        self._data[oid] = self._INTEGER(oid, value)

    def set_OCTETSTRING(self, oid, value):
        logger.debug('Setting OCTETSTRING %s = %s', oid, value)
        self._data[oid] = self._OCTETSTRING(oid, value)

    def set_OBJECTIDENTIFIER(self, oid, value):
        logger.debug('Setting OBJECTIDENTIFIER %s = %s', oid, value)
        self._data[oid] = self._OBJECTIDENTIFIER(oid, value)

    def set_IPADDRESS(self, oid, value):
        logger.debug('Setting IPADDRESS %s = %s', oid, value)
        self._data[oid] = self._IPADDRESS(oid, value)

    def set_COUNTER32(self, oid, value):
        logger.debug('Setting COUNTER32 %s = %s', oid, value)
        self._data[oid] = self._COUNTER32(oid, value)

    def set_GAUGE32(self, oid, value):
        logger.debug('Setting GAUGE32 %s = %s', oid, value)
        self._data[oid] = self._GAUGE32(oid, value)

    def set_TIMETICKS(self, oid, value):
        logger.debug('Setting TIMETICKS %s = %s', oid, value)
        self._data[oid] = self._TIMETICKS(oid, value)

    def set_OPAQUE(self, oid, value):
        logger.debug('Setting OPAQUE %s = %s', oid, value)
        self._data[oid] = self._OPAQUE(oid, value)

    def set_COUNTER64(self, oid, value):
        logger.debug('Setting COUNTER64 %s = %s', oid, value)
        self._data[oid] = self._COUNTER64(oid, value)


    @staticmethod
    def _INTEGER(oid, value):
        return {'name': oid, 'type':pyagentx3.TYPE_INTEGER, 'value':value}

    @staticmethod
    def _OCTETSTRING(oid, value):
        return {'name': oid, 'type':pyagentx3.TYPE_OCTETSTRING, 'value':value}

    @staticmethod
    def _OBJECTIDENTIFIER(oid, value):
        return {'name': oid, 'type':pyagentx3.TYPE_OBJECTIDENTIFIER, 'value':value}

    @staticmethod
    def _IPADDRESS(oid, value):
        return {'name': oid, 'type':pyagentx3.TYPE_IPADDRESS, 'value':value}

    @staticmethod
    def _COUNTER32(oid, value):
        return {'name': oid, 'type':pyagentx3.TYPE_COUNTER32, 'value':value}

    @staticmethod
    def _GAUGE32(oid, value):
        return {'name': oid, 'type':pyagentx3.TYPE_GAUGE32, 'value':value}

    @staticmethod
    def _TIMETICKS(oid, value):
        return {'name': oid, 'type':pyagentx3.TYPE_TIMETICKS, 'value':value}

    @staticmethod
    def _OPAQUE(oid, value):
        return {'name': oid, 'type':pyagentx3.TYPE_OPAQUE, 'value':value}

    @staticmethod
    def _COUNTER64(oid, value):
        return {'name': oid, 'type':pyagentx3.TYPE_COUNTER64, 'value':value}

