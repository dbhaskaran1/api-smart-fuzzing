'''
Contains the L{Harness} class for replaying function calls from a 
L{Trace} object in a controlled environment.

@author: Rob Waaser
@contact: robwaaser@gmail.com
@organization: Carnegie Mellon University
@since: October 26, 2011
'''

import multiprocessing
import ctypes
import sys
import os
import logging
from morpher.misc import log_setup

class Harness(multiprocessing.Process):
    '''
    Works as a seperate process which accepts a L{Trace}, loads a specified
    DLL, and uses the trace to replay a function call to the DLL.
    
    A fuzzer can't replay a L{Trace} in the same process because if the process
    crashes it will take down the fuzzer as well. Using the L{Harness} 
    allows the trace to be replayed in a seperate process, and if the process
    crashes a debugger can observe the crash and log any debug data. The 
    L{Harness} is deliberately kept as simple as possible - it merely
    accepts a L{Trace} from a pipe, replays each L{Snapshot} in the trace
    and reports successful completion for each using the pipe, then exits.
    
    Just before each L{Snapshot} is replayed, the harness sends a I{True} 
    value over the pipe it was given. This allows the process that owns the
    other end of the pipe to keep track of the L{Trace} replay's progress,
    so the exact L{Snapshot} that triggers a crash or hang can be pinpointed.
    
    @note: L{_kill_output} is used to suppress any output to standard output
           or standard error streams by the DLL during replay.
    
    @ivar cfg: The configuration object
    @ivar outpipe: The connection used to send "pings" back to the parent
    @ivar inpipe: The connection used to receive a L{Trace} object
    '''
    
    def __init__(self, cfg, pipe):
        '''
        Sets up the given input/output pipes and stores the config, which
        needs to be serializable. 
        
        @warning: This code is still in the same process as the object creator
        
        @param cfg: The configuration object with target and logging info
        @type cfg: L{Config} object
        
        @param pipe: A pair of L{multiprocessing} connections (input, output)
        @type pipe: (Connection, Connection) tuple
        '''
        multiprocessing.Process.__init__(self)
        self.cfg = cfg
        self.daemon = True
        (inpipe, outpipe) = pipe
        self.outpipe = outpipe
        self.inpipe = inpipe
        
    def run(self):
        '''
        Sets the seperate process running, waits for a L{Trace}, and
        replays the trace for the specified DLL.
        
        A seperate logging root is set up, with logging going to a 
        different file, so two processes won't be trying to write to
        the same file. The target DLL is loaded using information
        in the L{Config}, then the L{Harness} waits for a L{Trace}
        to be received over the pipe.
        
        After receiving the L{Trace}, the standard output is disabled
        and the trace is replayed one call at a time, with the value 
        I{True} being sent back over the pipe before each call to the
        DLL. Once the replay is complete the pipes are closed and 
        the process exits.
        '''
        # Set up a seperate logging root, since two processes 
        # shouldn't be writing to the same log file
        log_setup.setupLogging(self.cfg, __name__)
        self.log = logging.getLogger(__name__)
        self.log.info("Harness is running...")

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
        self._kill_output()
        debug = self.log.isEnabledFor(logging.DEBUG)
        if debug :
            self.log.debug("Received trace:\n\n%s\n", trace.toString())
        # Run each function capture in order
        for (name, args) in trace.replay() :
            self.log.info("Calling function %s", name)
            # Let Harness know we're about to make a call
            self.outpipe.send(True)
            # Make the call
            func = getattr(target, name)
            result = func(*args)
            self.log.info("Function returned result: %s", str(result))
        
        if debug :
            self.log.debug("Trace after calls:\n\n%s\n", trace.toString())
        self.log.info("Harness run complete, shutting down")
        self.outpipe.close()

    def _kill_output(self):
        '''
        Disables stdout and stderr for the DLL by redirecting those 
        descriptors to a NUL (fake) file, but restores the Python 
        interpreter's connection to stdout and stderr intact
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
        
       
        