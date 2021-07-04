# -*- coding: utf-8 -*-

# --------------------------------------------
import logging
class NullHandler(logging.Handler):
    def emit(self, record):
        pass
logger = logging.getLogger('pyagentx3.sethandler')
logger.addHandler(NullHandler())
# --------------------------------------------


class SetHandlerError(Exception):
    pass


class SetHandler():

    def __init__(self, data_store=None):
        self.data_store = data_store
        # A map of transactions to varbinds
        self.transactions = {}
        self._oid = None

    def agent_setup(self, oid):
        self._oid = oid

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
            # strip off leading oid
            oid = oid[len(self._oid) + 1:]
            self.testset(tid, self.transactions[tid])
        except SetHandlerError as e:
            logger.error('TestSet failed: %s', e)
            raise e

    def network_commit(self, session_id, transaction_id):
        tid = "%s_%s" % (session_id, transaction_id)
        if tid not in self.transactions:
            return
        try:
            self.commit(tid, self.transactions[tid])
            del self.transactions[tid]
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

