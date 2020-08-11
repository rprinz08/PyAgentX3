# -*- coding: utf-8 -*-

# --------------------------------------------
import logging
class NullHandler(logging.Handler):
    def emit(self, record):
        pass
logger = logging.getLogger('pyagentx3.network')
logger.addHandler(NullHandler())
# --------------------------------------------

import socket
import time
import threading
from queue import Empty
import pyagentx3
from pyagentx3.pdu import PDU


class Network(threading.Thread):

    def __init__(self, queue, oid_list, sethandlers, agent_id):
        threading.Thread.__init__(self)
        self.stop = threading.Event()
        self._agent_id = agent_id
        self._queue = queue
        self._oid_list = oid_list
        self._sethandlers = sethandlers

        self.session_id = 0
        self.transaction_id = 0
        self.debug = 1
        # Data Related Variables
        self.data = {}
        self.data_idx = []
        self.socket = None

    def _connect(self):
        while True:
            try:
                self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                self.socket.connect(pyagentx3.SOCKET_PATH)
                self.socket.settimeout(0.1)
                return
            except socket.error:
                logger.error("Failed to connect, sleeping and retrying later")
                time.sleep(2)

    def new_pdu(self, pdu_type):
        pdu = PDU(pdu_type, agent_id=self._agent_id)
        pdu.session_id = self.session_id
        pdu.transaction_id = self.transaction_id
        self.transaction_id += 1
        return pdu

    def response_pdu(self, org_pdu):
        pdu = PDU(pyagentx3.AGENTX_RESPONSE_PDU, agent_id=self._agent_id)
        pdu.session_id = org_pdu.session_id
        pdu.transaction_id = org_pdu.transaction_id
        pdu.packet_id = org_pdu.packet_id
        return pdu

    def send_pdu(self, pdu, force=False):
        log_level = logging.INFO if force else logging.DEBUG
        if self.debug or force:
            logger.log(log_level, "Send PDU:")
            pdu.dump()
        buf = pdu.encode()
        if self.debug or force:
            logger.log(log_level, buf)
        self.socket.send(buf)

    def recv_pdu(self):
        buf = self.socket.recv(1024)
        if not buf:
            return None
        pdu = PDU()
        pdu.decode(buf)
        if self.debug:
            logger.debug("Received PDU:")
            pdu.dump()
        return pdu

    # =========================================

    def _get_updates(self):
        while True:
            try:
                item = self._queue.get_nowait()
                #logger.info('Update: {}'.format(item))

                if 'oid' in item:
                    #logger.info('New update')
                    update_oid = item['oid']
                    update_data = item['data']
                    # clear values with prefix oid
                    for oid in list(self.data.keys()):
                        if oid.startswith(update_oid):
                            del self.data[oid]
                    # insert updated value
                    for row in list(update_data.values()):
                        oid = "%s.%s" % (update_oid, row['name'])
                        self.data[oid] = {'name': oid, 'type':row['type'],
                                        'value':row['value']}
                    # recalculate reverse index if data changed
                    self.data_idx = sorted(list(self.data.keys()),
                        key=lambda k: tuple(int(part) for part in k.split('.')))

                elif 'trap_oid' in item:
                    #logger.info('New traps')
                    trap_data = item['data']

                    if len(trap_data) > 0:
                        trap_pdu = self.new_pdu(pyagentx3.AGENTX_NOTIFY_PDU)
                        for row in list(trap_data.values()):
                            #logger.info(row)
                            trap_pdu.values.append(row)
                        trap_pdu.dump()
                        self.send_pdu(trap_pdu)

            except Empty:
                break

    def _get_next_oid(self, oid, endoid):
        if oid in self.data:
            # Exact match found
            #logger.debug('get_next_oid, exact match of %s' % oid)
            idx = self.data_idx.index(oid)
            if idx == (len(self.data_idx)-1):
                # Last Item in MIB, No match!
                return None
            return self.data_idx[idx+1]

        # No exact match, find prefix
        #logger.debug('get_next_oid, no exact match of %s' % oid)
        slist = oid.split('.')
        elist = endoid.split('.')
        for tmp_oid in self.data_idx:
            tlist = tmp_oid.split('.')
            for i in range(len(tlist)):
                try:
                    sok = int(slist[i]) <= int(tlist[i])
                except IndexError:
                    #sok = True, on most recent successful comparison
                    pass
                try:
                    eok = int(elist[i]) >= int(tlist[i])
                except IndexError:
                    #eok = True, on most recent successful comparison
                    pass
                if not (sok and eok):
                    break
            if sok and eok:
                return tmp_oid
        return None # No match!

    def start(self):
        while True:
            try:
                self._start_network()
            except socket.error:
                logger.error("Network error, master disconnect?!")

    def _start_network(self):
        self._connect()

        logger.info("==== Open PDU ====")
        pdu = self.new_pdu(pyagentx3.AGENTX_OPEN_PDU)
        self.send_pdu(pdu)
        pdu = self.recv_pdu()
        self.session_id = pdu.session_id

        logger.info("==== Ping PDU ====")
        pdu = self.new_pdu(pyagentx3.AGENTX_PING_PDU)
        self.send_pdu(pdu)
        pdu = self.recv_pdu()

        logger.info("==== Register PDU ====")
        for oid in self._oid_list:
            logger.info("Registering: %s", oid)
            pdu = self.new_pdu(pyagentx3.AGENTX_REGISTER_PDU)
            pdu.oid = oid
            self.send_pdu(pdu)
            pdu = self.recv_pdu()

        logger.info("==== Waiting for PDU ====")
        while True:
            try:
                self._get_updates()
                request = self.recv_pdu()
            except socket.timeout:
                continue

            if not request:
                logger.error("Empty PDU, connection closed!")
                raise socket.error

            response = self.response_pdu(request)
            if request.type == pyagentx3.AGENTX_GET_PDU:
                logger.info("Received GET PDU")
                for rvalue in request.range_list:
                    oid = rvalue[0]
                    logger.debug("OID: %s", oid)
                    if oid in self.data:
                        logger.debug("OID Found")
                        response.values.append(self.data[oid])
                    else:
                        logger.debug("OID Not Found!")
                        response.values.append({
                            'type': pyagentx3.TYPE_NOSUCHOBJECT,
                            'name': rvalue[0],
                            'value': 0})

            elif request.type == pyagentx3.AGENTX_GETNEXT_PDU:
                logger.info("Received GET_NEXT PDU")
                for rvalue in request.range_list:
                    oid = self._get_next_oid(rvalue[0], rvalue[1])
                    logger.debug("GET_NEXT: %s => %s", rvalue[0], oid)
                    if oid:
                        response.values.append(self.data[oid])
                    else:
                        response.values.append({
                            'type': pyagentx3.TYPE_ENDOFMIBVIEW,
                            'name': rvalue[0],
                            'value': 0})

            elif request.type == pyagentx3.AGENTX_TESTSET_PDU:
                logger.info("Received TESTSET PDU")
                idx = 0
                for row in request.values:
                    idx += 1
                    oid = row['name']
                    type_ = pyagentx3.TYPE_NAME.get(row['type'], 'Unknown type')
                    value = row['data']
                    logger.info("Name: [%s] Type: [%s] Value: [%s]", oid, type_, value)
                    # Find matching sethandler
                    matching_oid = ''
                    for target_oid in self._sethandlers:
                        if oid.startswith(target_oid):
                            matching_oid = target_oid
                            break
                    if matching_oid == '':
                        logger.debug('TestSet request failed: not writeable #%s', idx)
                        response.error = pyagentx3.ERROR_NOTWRITABLE
                        response.error_index = idx
                        break
                    try:
                        self._sethandlers[matching_oid].network_test(
                            request.session_id, request.transaction_id,
                            oid, row['data'])
                    except pyagentx3.SetHandlerError:
                        logger.debug('TestSet request failed: wrong value #%s', idx)
                        response.error = pyagentx3.ERROR_WRONGVALUE
                        response.error_index = idx
                        break
                logger.debug('TestSet request passed')


            elif request.type == pyagentx3.AGENTX_COMMITSET_PDU:
                for handler in list(self._sethandlers.values()):
                    handler.network_commit(request.session_id, request.transaction_id)
                logger.info("Received COMMITSET PDU")

            elif request.type == pyagentx3.AGENTX_UNDOSET_PDU:
                for handler in list(self._sethandlers.values()):
                    handler.network_undo(request.session_id, request.transaction_id)
                logger.info("Received UNDOSET PDU")

            elif request.type == pyagentx3.AGENTX_CLEANUPSET_PDU:
                for handler in list(self._sethandlers.values()):
                    handler.network_cleanup(request.session_id, request.transaction_id)
                logger.info("Received CLEANUP PDU")

            self.send_pdu(response)
