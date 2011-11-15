'''
Created on Oct 26, 2011

@author: Rob
'''

import multiprocessing
import ctypes
import sys
import os
import logging
from morpher.misc import log_setup

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
        self.daemon = True
        (inpipe, outpipe) = pipe
        self.outpipe = outpipe
        self.inpipe = inpipe
        
    def run(self):
        '''
        Receives a list of memory objects to call on 
        the target DLL
        '''
        log_setup.setupLogging(self.cfg, __name__)
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
            trace = self.inpipe.recv()
        except :
            self.log.exception("Error processing input from pipe")
            sys.exit()
            
        self.inpipe.close()
        
        # Take down stdout for the shared library
        self.kill_output()
        debug = self.log.isEnabledFor(logging.DEBUG)
        if debug :
            self.log.debug("Received trace:\n\n%s\n", trace.toString())
        # Run each function capture in order
        for (ordinal, args) in trace.replay() :
            self.log.info("Calling function ordinal %d", ordinal)
            # Let Harness know we're about to make a call
            self.outpipe.send(True)
            result = target[ordinal](*args)
            self.log.info("Function returned result: %s", str(result))
        
        if debug :
            self.log.debug("Trace after calls:\n\n%s\n", trace.toString())
        self.log.info("Harness run complete, shutting down")
        self.outpipe.close()

    def kill_output(self):
        '''
        Disables stdout and stderr for the DLL by redirecting to a NUL
        (fake) file, but keeps Python's stdout and stderr intact
        '''
        sys.stdout.flush() 
        sys.stderr.flush()
        # Save original version of stdout/err
        saved_out = os.dup(1)
        saved_err = os.dup(2)
        # Set stdout/err to fake device
        devnull = os.open('NUL', os.O_WRONLY)
        os.dup2(devnull, 1)
        os.dup2(devnull, 2)
        os.close(devnull)
        # Restore Python's stdout/err (library won't see this)
        sys.stdout = os.fdopen(saved_out, 'w')
        sys.stderr = os.fdopen(saved_err, 'w')
        
       
        