#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.insert(0,'..')

# --------------------------------------------
import logging
class NullHandler(logging.Handler):
    def emit(self, record):
        pass
logger = logging.getLogger('pyagentx3.main')
logger.addHandler(NullHandler())
# --------------------------------------------

import random
import datetime
import ipaddress
import pyagentx3


def str_to_oid(data):
    length = len(data)
    oid_int = [str(ord(i)) for i in data]
    return str(length) + '.' + '.'.join(oid_int)


class TestData():

    def __init__(self):
        self.sample_int = 9000
        self.sample_counter = 0
        self.boot_ts = datetime.datetime.now().timestamp()


class NetSnmpTestMibScalar(pyagentx3.Updater):

    def __init__(self, data_store=None):
        pyagentx3.Updater.__init__(self)
        self.data_store = data_store

    def update(self):
        # get new data
        self.data_store.sample_counter += 1
        now = datetime.datetime.now().timestamp()

        # Triggers a trap when counter is divisable by 5
        send_trap = 1 if (self.data_store.sample_counter % 5) == 0 else 0

        # Updated SNMP objects
        self.set_INTEGER('1.0', self.data_store.sample_int)

        # When send_trap != 0 triggers a trap configured in snmpd.conf monitoring when
        # following monitoring is configured there:
        #
        # monitor -S -I -r 2 \
        #   1.3.6.1.4.1.8072.2.3.0.1 \
        #   -o 1.3.6.1.4.1.8072.2.1.10.0 \
        #   1.3.6.1.4.1.8072.2.1.2.0 == 1
        #
        # Note: for this to work ensure that 'mteTrigger,mteTriggerConf' is not disabled
        # when snmpd starts (see either /etc/default/snmpd or systemctl edit snmpd --full)
        self.set_INTEGER('2.0', send_trap)

        self.set_OCTETSTRING('3.0', 'String for NET-SNMP-EXAMPLES-MIB')

        self.set_OBJECTIDENTIFIER('4.0', '1.3.6.1.4.6.7')

        self.set_IPADDRESS('5.0', ipaddress.ip_address('192.168.0.1'))

        # According to https://tools.ietf.org/html/rfc2465#section-3
        # an IPv6 address is represented as octetstring of length 16
        # with added textual conventions for output formating.
        # Note the 'packed' attribute
        #self.set_OCTETSTRING('3.0', ipaddress.ip_address('2001:db8:1000::42').packed)

        self.set_COUNTER32('6.0', 2000)

        self.set_GAUGE32('7.0', 2000)

        self.set_TIMETICKS('8.0', int((now * 100) - self.data_store.boot_ts * 100))

        self.set_OPAQUE('9.0', 'Test')

        self.set_COUNTER64('10.0', self.data_store.sample_counter)

        # Send trap directly via AgentX
        # Note: For traps to work ensure that you have configured a trap
        # destination in snmpd.conf. e.g:
        # trap2sink    localhost public
        if send_trap:
            logger.info('Counter trap [%s]', self.data_store.sample_counter)

            self.send_trap('1.3.6.1.4.1.8072.2.3.0.1',          # trap OID
                self._INTEGER('1.3.6.1.4.1.8072.2.3.2.1',       # payload 1 OID
                    self.data_store.sample_counter),            # payload 1 value
                self._OCTETSTRING('1.3.6.1.4.1.8072.2.3.2.2',   # payload N OID
                    'Counter is {}'.format(                     # payload N balue
                        self.data_store.sample_counter)))


class NetSnmpTestMibTable(pyagentx3.Updater):

    def __init__(self, data_store=None):
        pyagentx3.Updater.__init__(self)
        self.data_store = data_store

    def update(self):
        # Implement netSnmpIETFWGTable from NET-SNMP-EXAMPLES-MIB.txt
        # Number of entries in table is random to show that MIB is reset
        # on every update
        for i in range(random.randint(3, 5)):
            idx = str_to_oid('group%s' % (i + 1))
            self.set_OCTETSTRING('1.1.2.' + idx, 'member 1')
            self.set_OCTETSTRING('1.1.3.' + idx, 'member 2')


class NetSnmpIntegerSet(pyagentx3.SetHandler):

    def test(self, oid, data):
        if int(data) > 100:
            raise pyagentx3.SetHandlerError()

    def commit(self, oid, data):
        print("COMMIT CALLED: %s = %s" % (oid, data))
        self.data_store.sample_int = data


class SampleAgent(pyagentx3.Agent):

    def __init__(self, agent_id='SampleAgent', socket_path=None):
        super().__init__(agent_id, socket_path)

    def setup(self):
        data = TestData()

        self.register('1.3.6.1.4.1.8072.2.1',
            NetSnmpTestMibScalar, freq=10, data_store=data)

        self.register('1.3.6.1.4.1.8072.2.2',
            NetSnmpTestMibTable, freq=5, data_store=data)

        self.register_set('1.3.6.1.4.1.8072.2.1.1.0',
            NetSnmpIntegerSet, data_store=data)


def main():
    pyagentx3.setup_logging(debug=False)

    try:
        agt = SampleAgent()
        agt.start()
    except Exception as ex:
        print("Unhandled exception: %s" % ex)
        agt.stop()
    except KeyboardInterrupt:
        agt.stop()

if __name__ == "__main__":
    main()

