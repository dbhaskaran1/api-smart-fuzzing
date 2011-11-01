'''
Created on Oct 26, 2011

@author: Rob
'''

import multiprocessing
import ctypes
import sys
import logging
from morpher.misc import logsetup

class Harness(multiprocessing.Process):
    '''
    classdocs
    '''
    
    def __init__(self, cfg, pipe):
        '''
        Sets up pipes and config. NOT IN NEW PROCESS YET
        '''
        multiprocessing.Process.__init__(self)
        self.cfg = cfg
        (inpipe, outpipe) = pipe
        self.outpipe = outpipe
        self.inpipe = inpipe
        
    def run(self):
        '''
        Receives a list of memory objects to call on 
        the target DLL
        '''
        logsetup.setupLogging(self.cfg, __name__)
        self.log = logging.getLogger(__name__)
        self.log.info("Harness is running...")
        
        #self.outpipe.close()
        
        dlltype = self.cfg.get('fuzzer', 'dll_type')
        path = self.cfg.get('fuzzer', 'target')
        
        # Load the target DLL
        if dlltype == "cdecl" :
            dll = ctypes.cdll
        else :
            dll = ctypes.windll
        target = dll.LoadLibrary(path)
        
        self.log.info("DLL loaded, waiting for trace")
        
        # Wait for the list to be sent. By the time this happens hooks
        # should be set and debugger ready for us to run the trace
        try :
            mlist = self.inpipe.recv()
        except :
            self.log.exception("Error processing input from pipe")
            sys.exit()
            
        self.inpipe.close()
        
        debug = self.log.isEnabledFor(logging.DEBUG)
        # Run each function capture in order
        for m in mlist :
            m.patch()
            args = m.getArgs()
            ordinal = m.ordinal
            self.log.info("Calling function ordinal %d", ordinal)
            if debug :
                self.log.debug(m.toString())
            # Let Harness know we're about to make a call
            self.outpipe.send(True)

            result = target[ordinal](*args)
            self.log.info("Function returned result: %s", str(result))
            if debug :
                self.log.debug("Memory contents after function call:")
                self.log.debug(m.toString())
            
        self.log.info("Harness run complete, shutting down")
        self.outpipe.close()
            
        
       
        