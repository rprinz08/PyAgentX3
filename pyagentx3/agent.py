# -*- coding: utf-8 -*-

# --------------------------------------------
import logging
class NullHandler(logging.Handler):
    def emit(self, record):
        pass
logger = logging.getLogger('pyagentx3.agent')
logger.addHandler(NullHandler())
# --------------------------------------------

import time
from queue import Queue
import inspect
import pyagentx3
from pyagentx3.updater import Updater
from pyagentx3.network import Network


class AgentError(Exception):
    pass


class Agent():

    def __init__(self, agent_id='MyAgent'):
        self.agent_id = agent_id
        self._updater_list = []
        self._sethandlers = {}
        self._threads = []

    def register(self, oid, class_, freq=10, data_store=None):
        if Updater not in inspect.getmro(class_):
            raise AgentError('Class given isn\'t an updater')

        # cleanup and test oid
        try:
            oid = oid.strip(' .')
            _ = [int(i) for i in oid.split('.')]
        except ValueError:
            raise AgentError('OID isn\'t valid')
        self._updater_list.append({
            'oid': oid,
            'class': class_,
            'data_store': data_store,
            'freq': freq})

    def register_set(self, oid, class_, data_store=None):
        if pyagentx3.SetHandler not in class_.__bases__:
            raise AgentError('Class given isn\'t a SetHandler')

        # cleanup and test oid
        try:
            oid = oid.strip(' .')
            _ = [int(i) for i in oid.split('.')]
        except ValueError:
            raise AgentError('OID isn\'t valid')
        self._sethandlers[oid] = class_(data_store=data_store)

    def setup(self):
        # Override this
        pass

    def start(self):
        queue = Queue(maxsize=20)
        self.setup()

        # Start Updaters
        for u in self._updater_list:
            logger.debug('Starting updater [%s]', u['oid'])
            thread = u['class'](data_store=u['data_store'])
            thread.agent_setup(queue, u['oid'], u['freq'])
            thread.start()
            self._threads.append(thread)

        # Start Network
        oid_list = [u['oid'] for u in self._updater_list]
        thread = Network(queue, oid_list, self._sethandlers, self.agent_id)
        thread.start()
        self._threads.append(thread)

        # Do nothing ... just wait for someone to stop you
        while True:
            #logger.debug('Agent Sleeping ...')
            time.sleep(1)

    def stop(self):
        logger.debug('Stop threads')
        for thread in self._threads:
            thread.stop.set()
        logger.debug('Wait for updater')
        for thread in self._threads:
            thread.join()

