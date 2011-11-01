'''
Created on Oct 21, 2011

@author: Rob
'''

from parser import parser
from collector import collector
from fuzzer import fuzzer
from misc import config, logsetup
import logging

class Morpher(object):
    '''
    The top-level object for the Morpher tool
    '''

    def __init__(self, **params):
        '''
        Sets up a Config object for this morpher and initializes
        the logging system

        @type  params:      Variable
        @param params:      Name-value pairs
        '''
        # The config object used for configuration info
        self.cfg = config.Config(**params)
        logsetup.setupLogging(self.cfg)
        # The logging object used for reporting
        self.log = logging.getLogger(__name__)
        self.log.info(self.cfg.toString())
    
    def run(self):
        '''
        Runs the morpher program
        '''
        # Run the parser
        p = parser.Parser(self.cfg)
        p.parse()
        # Run the collector
        c = collector.Collector(self.cfg)
        c.collect()
        # Fuzz the traces and replay them
        f = fuzzer.Fuzzer(self.cfg)
        f.fuzz()

