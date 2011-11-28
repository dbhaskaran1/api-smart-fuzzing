'''
Contains the L{Morpher} class for intelligently fuzzing Application
Programming Interface (API) calls to third-party DLLs.

@author: Rob Waaser
@contact: robwaaser@gmail.com
@organization: Carnegie Mellon University
@since: October 21, 2011
'''

from parser import parser
from collector import collector
from fuzzer import fuzzer
from misc import config, log_setup
import logging
import os

class Morpher(object):
    '''
    The top-level object for the Morpher tool.
    
    Morpher is executed in three consecutive, mostly seperate
    phases: parsing, collecting, and fuzzing. The functionality
    of these three phases is performed by seperate classes (the
    L{Parser}, L{Collector}, and L{Fuzzer} classes respectively).
    The L{Morpher} class doesn't actually perform a lot of 
    functionality - it is mainly responsible for coordinating these
    three phases and providing a top-level object for the whole
    process.
    
    @ivar cfg: The L{Config} object
    @ivar log: The L{logging} object
    
    @todo: Add an option to disable printing messages/status bar
    '''

    def __init__(self, **params):
        '''
        Sets up a L{Config} object for this morpher and initializes
        the L{logging} system. Almost all other objects that make up
        Morpher will share a reference to this same L{Config} object.

        @type  params: Parameters to override the configuration with
        @param params: dictionary
        '''
        # The config object used for configuration info
        self.cfg = config.Config(**params)
        log_setup.setupLogging(self.cfg)
        # The logging object used for reporting
        self.log = logging.getLogger(__name__)
        self.log.info(self.cfg.toString())
    
    def run(self):
        '''
        Runs the Morpher program. The Morpher tool is implemented by
        instantiating a L{Parser} object, a L{Collector} object, and a
        L{Fuzzer} object and running their respective main functions in
        order. This function is mainly just responsible for triggering the
        three main phases of the tool in order and displaying appropriate
        output to the console.
        '''
        dllname = self.cfg.get('fuzzer','target')
        dllname = os.path.split(dllname)[1]
        
        print "\n\n  Welcome to Morpher, the Automatic Mutational API Fuzzer"
        print "  =======================================================\n"
        
        print "  Current Target: %s" % dllname
        print "  See the log files for more details\n"
        print "  Launching Morpher chain, please wait:\n"
        # Run the parser
        p = parser.Parser(self.cfg)
        p.parse()
        # Run the collector
        c = collector.Collector(self.cfg)
        c.collect()
        # Fuzz the traces and replay them
        f = fuzzer.Fuzzer(self.cfg)
        f.fuzz()
        
        print "\n  Morpher run complete.\n"
