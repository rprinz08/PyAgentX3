# -*- coding: utf-8 -*-

# --------------------------------------------
import logging
class NullHandler(logging.Handler):
    def emit(self, record):
        pass
logger = logging.getLogger('pyagentx3.sethandler')
logger.addHandler(NullHandler())
# --------------------------------------------


from queue import Full

import pyagentx3


class SetHandlerError(Exception):
    pass


class SetHandler():

    def __init__(self, data_store=None):
        self.data_store = data_store
        # A map of transactions to varbinds
        self.transactions = {}
        self._oid = None
        self._data = {}

    def agent_setup(self, queue, oid):
        self._queue = queue
        self._oid = oid
        self._data = {}

    def network_test(self, session_id, transaction_id, oid, data):
        tid = "%s_%s" % (session_id, transaction_id)
        if tid not in self.transactions:
            self.transactions[tid] = []
        try:
            # strip off leading oid
            oid = oid[len(self._oid) + 1:]
            self.test(tid, oid, data)
            self.transactions[tid].append((oid, data))
        except SetHandlerError as e:
            logger.error('TestSet failed: %s', e)
            raise e

    def network_testset(self, session_id, transaction_id):
        tid = "%s_%s" % (session_id, transaction_id)
        try:
            self.testset(tid, self.transactions[tid])
        except SetHandlerError as e:
            logger.error('TestSet failed: %s', e)
            raise e

    def network_commit(self, session_id, transaction_id):
        tid = "%s_%s" % (session_id, transaction_id)
        if tid not in self.transactions:
            return
        self._data = {}
        try:
            self.commit(tid, self.transactions[tid])
            del self.transactions[tid]
            self._queue.put_nowait({'oid': self._oid,
                                    'data': self._data})
        except Full:
            logger.error('Queue full')
        except Exception as e:
            logger.error('CommitSet failed: %s', e)

    def network_undo(self, session_id, transaction_id):
        tid = "%s_%s" % (session_id, transaction_id)
        if tid in self.transactions:
            del self.transactions[tid]

    def network_cleanup(self, session_id, transaction_id):
        tid = "%s_%s" % (session_id, transaction_id)
        if tid in self.transactions:
            del self.transactions[tid]

    # User override these
    def test(self, tid, oid, data):
        """Test individual varbinds in a transaction."""
        pass

    def testset(self, tid):
        """Test whole set after all varbinds have been tested."""
        pass

    def commit(self, tid, oid, data):
        pass

    def set_INTEGER(self, oid, value):
        logger.debug('Setting INTEGER %s = %s', oid, value)
        self._data[oid] = self._INTEGER(oid, value)

    def set_OCTETSTRING(self, oid, value):
        logger.debug('Setting OCTETSTRING %s = %s', oid, value)
        self._data[oid] = self._OCTETSTRING(oid, value)

    @staticmethod
    def _INTEGER(oid, value):
        return {'name': oid, 'type':pyagentx3.TYPE_INTEGER, 'value':value}

    @staticmethod
    def _OCTETSTRING(oid, value):
        return {'name': oid, 'type':pyagentx3.TYPE_OCTETSTRING, 'value':value}
