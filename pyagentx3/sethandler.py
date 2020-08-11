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
        self.transactions = {}

    def network_test(self, session_id, transaction_id, oid, data):
        tid = "%s_%s" % (session_id, transaction_id)
        if tid in self.transactions:
            del self.transactions[tid]
        try:
            self.test(oid, data)
            self.transactions[tid] = oid, data
        except SetHandlerError as e:
            logger.error('TestSet failed: %s', e)
            raise e

    def network_commit(self, session_id, transaction_id):
        tid = "%s_%s" % (session_id, transaction_id)
        if tid not in self.transactions:
            return
        try:
            oid, data = self.transactions[tid]
            self.commit(oid, data)
            if tid in self.transactions:
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
    def test(self, oid, data):
        pass

    def commit(self, oid, data):
        pass

