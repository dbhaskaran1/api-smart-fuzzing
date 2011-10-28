'''
Created on Oct 26, 2011

@author: Rob
'''

import multiprocessing
import ctypes
import sys
import logging

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
        self.cfg.setupLogging(__name__)
        self.log = self.cfg.getLogger(__name__)
        self.log.info("Harness is running...")
        
        self.outpipe.close()
        
        dlltype = self.cfg.get('fuzzer', 'dlltype')
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
        
        # Run each function capture in order
        for m in mlist :
            args = m.getArgs()
            ordinal = m.ordinal
            self.log.info("Calling function ordinal %d", ordinal)
            if self.cfg.logLevel() == logging.DEBUG :
                self.log.debug(m.toString())
            result = target[ordinal](*args)
            self.log.info("Function returned result: %s", str(result))
            
        self.log.info("Harness run complete, shutting down")
            
        
       
        