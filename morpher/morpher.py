'''
Created on Oct 21, 2011

@author: Rob
'''

import parser.parser as parser
# import collector.collector as collector
import misc.config as config


class Morpher:
    '''
    The top-level object for the Morpher tool
    '''
    
    cfg = None
    log = None
    
    def __init__(self, **params):
        '''
        Sets up a Config object for this morpher and initializes
        the logging system

        @type  params:      Variable
        @param params:      Name-value pairs
        '''
        self.cfg = config.Config(**params)
        self.cfg.setupLogging()
        self.cfg.logConfig()
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
