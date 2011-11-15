'''
Created on Oct 28, 2011

@author: Rob
'''
import os
from morpher.collector import func_recorder
from morpher.pydbg import pydbg, defines
from morpher.trace import trace
import logging
import threading

class TraceRecorder(object):
    '''
    classdocs
    '''

    def __init__(self, cfg, model):
        '''
        Constructor
        '''
        # The Config object used for configuration info
        self.cfg = cfg
        # The logging object used for reporting
        self.log = logging.getLogger(__name__)
        # The xml model used for traversal
        self.model = model
        # The target dll
        self.dllpath = self.cfg.get('fuzzer', 'target')
        # The trace
        self.trace = []
        # The number of seconds until we declare a timeout
        self.limit = cfg.getint('collector', 'timeout')
        # Function recorder
        self.func_recorder = func_recorder.FuncRecorder(cfg, model)
    
    def record(self, exe, arg):
        '''
        Given an application that uses the target DLL and an XML
        model tree, record a trace of dll function calls
        '''
        self.log.info("Running collection line: exe - %s  arg - %s", exe, arg)
        # Clear the trace recording
        self.trace = []
        # Load the application in a debugger
        self.log.info("Loaded program, setting breakpoints")
        self.dbg = pydbg.pydbg()
        self.dbg.load(exe, command_line=arg, create_new_console=True, show_window=False)
        # Set breakpoints on functions
        self.dbg.set_callback(defines.LOAD_DLL_DEBUG_EVENT, self.loadHandler)
        self.dbg.set_callback(defines.USER_CALLBACK_DEBUG_EVENT, self.checkTimeout)
          
        self.timed_out = False
        t = threading.Timer(self.limit, self.timeoutHandler)
          
        self.log.info("Running the program")
        t.start()
        self.dbg.run()
        t.cancel()
        
        newtrace = trace.Trace(self.model, self.trace)
        
        return newtrace
    
    def checkTimeout(self, dbg):
        '''
        Checks for timeouts, in which case it logs the hang and terminates the process.
        Set as handler for debugger's event loop (called at least every 100ms)
        '''
        if self.timed_out :
            # Terminate the process
            self.log.info("!!! Harness timed out !!!")
            self.log.info("Terminating harness")
            dbg.terminate_process() 
    
    def timeoutHandler(self):
        '''
        Sets the timed_out flag. Should call with a timer after (MAXTIME) seconds
        '''
        self.timed_out = True
        
    def loadHandler(self,dbg):
        '''
        Activated when the target library is loaded by the application - goes 
        through and sets hooks in each known function to call func_handler
        '''
        last_dll = dbg.get_system_dll(-1)
        self.log.debug("Caught event loading: %s from %s into: %08x size: %d", \
                       last_dll.name, last_dll.path, last_dll.base, last_dll.size)
        dllname =  os.path.split(self.dllpath)[1]
        if last_dll.name == dllname:
            self.log.info("Setting breakpoints for dll %s", dllname)
            for node in self.model.getElementsByTagName("function") :
                ordinal = int(node.getAttribute("ordinal"))
                address = dbg.func_resolve(self.dllpath, ordinal)
                self.log.debug("Setting breakpoint: dll %s ordinal %d address %x", dllname, ordinal, address)
                desc = str(ordinal)
                dbg.bp_set(address, description=desc, handler=self.funcHandler)
                self.log.debug("Breakpoint set at address %x", address)
        
        return defines.DBG_CONTINUE 
        
    def funcHandler(self,dbg):
        '''
        Activated upon a function call. Determines which function was called
        and starts the snapshot process to capture the function arguments
        '''
        self.log.debug("Breakpoint tripped, address %x", dbg.context.Eip)
        ordinal = int(dbg.breakpoints[dbg.context.Eip].description)
        snap = self.func_recorder.record(dbg, ordinal)
        self.trace.append(snap)          
        
        return defines.DBG_CONTINUE 