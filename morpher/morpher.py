'''
Created on Oct 21, 2011

@author: Rob
'''

from parser import parser
# import collector.collector as collector
from misc import config


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
        self.cfg.setupLogging()
        self.cfg.logConfig()
        # The logging object used for reporting
        self.log = self.cfg.getLogger(__name__)

    
    def run(self):
        '''
        Runs the morpher program
        '''
        # Run the parser
        p = parser.Parser(self.cfg)
        p.parse()
        # Run the collector
        #collector.collect()
    
        '''
        fuzz = fuzzer.fuzzer(dll)
        fuzz.start()
        pid = fuzz.pid
        '''
