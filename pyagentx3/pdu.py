# -*- coding: utf-8 -*-

# --------------------------------------------
import logging
class NullHandler(logging.Handler):
    def emit(self, record):
        pass
logger = logging.getLogger('pyagentx3.pdu')
logger.addHandler(NullHandler())
# --------------------------------------------

import struct
from ipaddress import IPv4Address, IPv6Address
import collections
import pprint
import pyagentx3
from pyagentx3.tools import hexdump


class PDU(object):

    def __init__(self, pdu_type=0, agent_id='MyAgent'):
        self.type = pdu_type
        self.agent_id = agent_id
        self.session_id = 0
        self.transaction_id = 0
        self.packet_id = 0
        self.error = pyagentx3.ERROR_NOAGENTXERROR
        self.error_index = 0
        self.decode_buf = ''
        self.state = {}
        self.values = []

    def dump(self, force=False):
        log_level = logging.INFO if force else logging.DEBUG
        name = pyagentx3.PDU_TYPE_NAME[self.type]
        logger.log(log_level, 'PDU DUMP: New PDU')
        logger.log(log_level, 'PDU DUMP: Meta      : [%s: %d %d %d]',
                                                name, self.session_id,
                                                self.transaction_id,
                                                self.packet_id)

        if 'payload_length' in self.state:
            logger.log(log_level, 'PDU DUMP: Length    : %s', self.state['payload_length'])

        if hasattr(self, 'response'):
            logger.log(log_level, 'PDU DUMP: Response  : %s', self.response)

        if hasattr(self, 'values'):
            logger.log(log_level, 'PDU DUMP: Values    : %s', pprint.pformat(self.values))

        if hasattr(self, 'range_list'):
            logger.log(log_level, 'PDU DUMP: Range list: %s', pprint.pformat(self.range_list))

    # ====================================================
    # encode functions

    def encode_oid(self, oid, include=0):
        oid = oid.strip()
        oid = oid.split('.')
        oid = [int(i) for i in oid]
        if len(oid) > 5 and oid[:4] == [1, 3, 6, 1]:
            # prefix
            prefix = oid[4]
            oid = oid[5:]
        else:
            # no prefix
            prefix = 0
        buf = struct.pack('BBBB', len(oid), prefix, include, 0)
        for i in range(len(oid)):
            buf += struct.pack('!L', oid[i])
        return buf

    def encode_octet(self, octet):
        data_len = 0
        data = octet

        if not isinstance(octet, collections.Sized):
            if isinstance(octet, IPv4Address) or isinstance(octet, IPv6Address):
                data = octet.packed
            else:
                data = str(octet)

        if isinstance(data, str):
            data = data.encode('latin1')

        data_len = len(data)
        buf = struct.pack('!L', data_len)

        buf += bytearray(data)

        padding = -data_len % 4
        buf += bytearray([0] * padding)
        return buf

    def encode_value(self, pdu_type, name, value):
        buf = struct.pack('!HH', pdu_type, 0)
        buf += self.encode_oid(name)

        if pdu_type in [pyagentx3.TYPE_INTEGER]:
            buf += struct.pack('!l', value)

        elif pdu_type in [pyagentx3.TYPE_COUNTER32,
                          pyagentx3.TYPE_GAUGE32,
                          pyagentx3.TYPE_TIMETICKS]:
            buf += struct.pack('!L', value)

        elif pdu_type in [pyagentx3.TYPE_COUNTER64]:
            buf += struct.pack('!Q', value)

        elif pdu_type in [pyagentx3.TYPE_OBJECTIDENTIFIER]:
            buf += self.encode_oid(value)

        elif pdu_type in [pyagentx3.TYPE_IPADDRESS,
                          pyagentx3.TYPE_OPAQUE,
                          pyagentx3.TYPE_OCTETSTRING]:
            buf += self.encode_octet(value)

        elif pdu_type in [pyagentx3.TYPE_NULL,
                          pyagentx3.TYPE_NOSUCHOBJECT,
                          pyagentx3.TYPE_NOSUCHINSTANCE,
                          pyagentx3.TYPE_ENDOFMIBVIEW]:
            # No data
            pass
        else:
            logger.error('Unknown Type: %s', pdu_type)
        return buf

    def encode_header(self, pdu_type, payload_length=0, flags=0):
        flags = flags | 0x10  # Bit 5 = all ints in NETWORK_BYTE_ORDER
        buf = struct.pack('BBBB', 1, pdu_type, flags, 0)
        buf += struct.pack('!L', self.session_id) # sessionID
        buf += struct.pack('!L', self.transaction_id) # transactionID
        buf += struct.pack('!L', self.packet_id) # packetID
        buf += struct.pack('!L', payload_length)
        return buf

    def encode(self):
        buf = b''
        if self.type == pyagentx3.AGENTX_OPEN_PDU:
            # timeout
            buf += struct.pack('!BBBB', 5, 0, 0, 0)
            # agent OID
            buf += struct.pack('!L', 0)
            # Agent Desc
            buf += self.encode_octet(self.agent_id)

        elif self.type == pyagentx3.AGENTX_PING_PDU:
            # No extra data
            pass

        elif self.type == pyagentx3.AGENTX_REGISTER_PDU:
            range_subid = 0
            timeout = 5
            priority = 127
            buf += struct.pack('BBBB', timeout, priority, range_subid, 0)
            # Sub Tree
            buf += self.encode_oid(self.oid)

        elif self.type == pyagentx3.AGENTX_RESPONSE_PDU:
            buf += struct.pack('!LHH', 0, self.error, self.error_index)
            for value in self.values:
                buf += self.encode_value(value['type'], value['name'], value['value'])

        elif self.type == pyagentx3.AGENTX_NOTIFY_PDU:
            for value in self.values:
                buf += self.encode_value(value['type'], value['name'], value['value'])

        else:
            # Unsupported PDU type
            pass

        encoded_pdu = self.encode_header(self.type, len(buf)) + buf

        logger.debug('Encoded AgentX PDU:')
        for i in hexdump(encoded_pdu, sep='-'):
            logger.debug(i)

        return encoded_pdu


    # ====================================================
    # decode functions

    def set_decode_buf(self, buf):
        self.decode_buf = buf

    def decode_oid(self):
        try:
            t = struct.unpack('!BBBB', self.decode_buf[:4])
            self.decode_buf = self.decode_buf[4:]
            ret = {
                'n_subid': t[0],
                'prefix':t[1],
                'include':t[2],
                'reserved':t[3],
            }
            sub_ids = []
            if ret['prefix']:
                sub_ids = [1, 3, 6, 1]
                sub_ids.append(ret['prefix'])
            for i in range(ret['n_subid']):
                t = struct.unpack('!L', self.decode_buf[:4])
                self.decode_buf = self.decode_buf[4:]
                sub_ids.append(t[0])
            oid = '.'.join(str(i) for i in sub_ids)
            return oid, ret['include']
        except Exception:
            logger.exception('Invalid packing OID header')
            logger.debug('%s', pprint.pformat(self.decode_buf))

    def decode_search_range(self):
        start_oid, include = self.decode_oid()
        if start_oid == []:
            return [], [], 0
        end_oid, _ = self.decode_oid()
        return start_oid, end_oid, include

    def decode_search_range_list(self):
        range_list = []
        while len(self.decode_buf):
            range_list.append(self.decode_search_range())
        return range_list

    def decode_octet(self):
        try:
            t = struct.unpack('!L', self.decode_buf[:4])
            l = t[0]
            buf = b''
            self.decode_buf = self.decode_buf[4:]
            if l > 0:
                padding = -l % 4
                buf = self.decode_buf[:l]
                self.decode_buf = self.decode_buf[l+padding:]
            return buf
        except Exception:
            logger.exception('Invalid packing octet header')

    def decode_value(self):
        ok = True
        vtype = None
        oid = None
        data = None

        try:
            vtype, _ = struct.unpack('!HH', self.decode_buf[:4])
            self.decode_buf = self.decode_buf[4:]
        except Exception:
            logger.exception('Unable to unpack value header')
            ok = False

        if ok:
            try:
                oid, _ = self.decode_oid()
            except Exception:
                logger.exception('Unable to decode OID for value type (%s %s)',
                    vtype, pyagentx3.TYPE_NAME.get(vtype, 'UNKNOWN'))
                ok = False

        if ok:
            try:
                if vtype in [pyagentx3.TYPE_INTEGER,
                            pyagentx3.TYPE_COUNTER32,
                            pyagentx3.TYPE_GAUGE32,
                            pyagentx3.TYPE_TIMETICKS]:
                    data = struct.unpack('!L', self.decode_buf[:4])
                    data = data[0]
                    self.decode_buf = self.decode_buf[4:]

                elif vtype in [pyagentx3.TYPE_COUNTER64]:
                    data = struct.unpack('!Q', self.decode_buf[:8])
                    data = data[0]
                    self.decode_buf = self.decode_buf[8:]

                elif vtype in [pyagentx3.TYPE_OBJECTIDENTIFIER]:
                    data, _ = self.decode_oid()

                elif vtype in [pyagentx3.TYPE_IPADDRESS,
                            pyagentx3.TYPE_OPAQUE,
                            pyagentx3.TYPE_OCTETSTRING]:
                    data = self.decode_octet()

                elif vtype in [pyagentx3.TYPE_NULL,
                            pyagentx3.TYPE_NOSUCHOBJECT,
                            pyagentx3.TYPE_NOSUCHINSTANCE,
                            pyagentx3.TYPE_ENDOFMIBVIEW]:
                    # No data
                    data = None

                else:
                    logger.error('Unknown value type (%s)', vtype)
                    ok = False

            except Exception:
                logger.exception('Unable to decode value of type (%d %s) for OID (%s)',
                    vtype, pyagentx3.TYPE_NAME.get(vtype, 'UNKNOWN'), oid)
                ok = False

        return {'type':vtype, 'name':oid, 'data':data}, ok

    def decode_header(self):
        try:
            t = struct.unpack('!BBBBLLLL', self.decode_buf[:20])
            self.decode_buf = self.decode_buf[20:]
            ret = {
                'version': t[0],
                'pdu_type':t[1],
                'pdu_type_name':  pyagentx3.PDU_TYPE_NAME[t[1]],
                'flags':t[2],
                'reserved':t[3],
                'session_id':t[4],
                'transaction_id':t[5],
                'packet_id':t[6],
                'payload_length':t[7],
            }
            self.state = ret
            self.type = ret['pdu_type']
            self.session_id = ret['session_id']
            self.packet_id = ret['packet_id']
            self.transaction_id = ret['transaction_id']
            self.decode_buf = self.decode_buf[:ret['payload_length']]
            if ret['flags'] & 0x08:  # content present
                context = self.decode_octet()
                logger.debug('Context: %s', context)
            return ret
        except Exception:
            logger.exception('Invalid packing: %d', len(self.decode_buf))
            logger.debug('%s', pprint.pformat(self.decode_buf))

    def decode(self, buf):
        self.set_decode_buf(buf)

        logger.debug('Decode AgentX PDU:')
        for i in hexdump(self.decode_buf, sep='-'):
            logger.debug(i)

        ret = self.decode_header()
        if ret['pdu_type'] == pyagentx3.AGENTX_RESPONSE_PDU:
            # Decode Response Header
            t = struct.unpack('!LHH', self.decode_buf[:8])
            self.decode_buf = self.decode_buf[8:]
            self.response = {
                'sysUpTime': t[0],
                'error':t[1],
                'error_name':pyagentx3.ERROR_NAMES[t[1]],
                'index':t[2],
            }
            # Decode VarBindList
            self.values = []
            while len(self.decode_buf):
                data, ok = self.decode_value()
                if ok:
                    self.values.append(data)

        elif ret['pdu_type'] == pyagentx3.AGENTX_GET_PDU:
            self.range_list = self.decode_search_range_list()

        elif ret['pdu_type'] == pyagentx3.AGENTX_GETNEXT_PDU:
            self.range_list = self.decode_search_range_list()

        elif ret['pdu_type'] == pyagentx3.AGENTX_TESTSET_PDU:
            # Decode VarBindList
            self.values = []
            while len(self.decode_buf):
                data, ok = self.decode_value()
                if ok:
                    self.values.append(data)

        elif ret['pdu_type'] in [pyagentx3.AGENTX_COMMITSET_PDU,
                                 pyagentx3.AGENTX_UNDOSET_PDU,
                                 pyagentx3.AGENTX_CLEANUPSET_PDU]:
            pass

        else:
            pdu_type_str = pyagentx3.PDU_TYPE_NAME.get(ret['pdu_type'],
                'Unknown:'+ str(ret['pdu_type']))
            logger.error('Unsupported PDU type: %s', pdu_type_str)

