'''
Contains the L{TraceRecorder} class for creating a L{Trace} by 
observing a program using a DLL

@author: Rob Waaser
@contact: robwaaser@gmail.com
@organization: Carnegie Mellon University
@since: October 28, 2011
'''

import os
from morpher.collector import func_recorder
from morpher.pydbg import pydbg, defines
from morpher.trace import trace
import logging
import threading

class TraceRecorder(object):
    '''
    Used to run a program and produce a L{Trace} object that can replay
    all function calls to the target DLL observed during the program run.
    Stores enough information to hook function calls using the supplied
    model and configuration objects and uses a L{FuncRecorder} to do 
    the actual stack recording.
    
    @ivar cfg: The L{Config} object
    @ivar log: The L{logging} object
    @ivar model: The XML root L{Node} for the DLL model
    @ivar dllpath: Path to the target DLL
    @ivar trace: The list of L{Snapshot} objects to turn into a L{Trace}
    @ivar limit: The number of seconds a program can run before its 
                 considered to have timed out
    @ivar copy_limit: The max number of times a particular function call
                      should be recorded
    @ivar global_limit: Whether the copy limit is across all traces
    @ivar copies: A table recording the number of snapshots per function
    @ivar collected: Set containing all functions recorded by this object
    @ivar func_recorder: L{FuncRecorder} object used for stack capture
    '''

    def __init__(self, cfg, model):
        '''
        Stores the configuration object and model for local use and
        initializes other instance variables
        
        @param cfg: The configuration object to use
        @type cfg: L{Config} object
        
        @param model: The root node of the XML DLL model 
        @type model: L{Node} object
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
        # The number of copies of a single function call
        self.copy_limit = cfg.getint('collector', 'copy_limit')
        # Whether this is a global limit or per-trace
        self.global_limit = cfg.getboolean('collector', 'global_limit')
        # Table of how many snapshots of each function have been taken
        self.copies = {}
        # Set of unique functions recorded
        self.collected = set()
        # Function recorder
        self.func_recorder = func_recorder.FuncRecorder(cfg, model)
    
    def record(self, exe, arg):
        '''
        Given an application that uses the target DLL, runs the program
        and captures a L{Trace} object thats capable of replaying all the
        function calls made by the application to the DLL.
        
        The L{Trace} is captured by launching the application in a second
        process and setting breakpoints at the beginning of each of the
        functions in the DLL. The application is allowed to run and if 
        any of the breakpoints are tripped, a L{FuncRecorder} is used 
        along with the debugger to capture all relevant areas of the stack.
        Each L{Snapshot} is stored in the created L{Trace} in the same
        order that they were captured in.
        
        @param exe: The path to the application to record.    
        @type exe: string
        
        @param arg: List of command-line arguments for the program
        @type arg: string
        
        @return: A L{Trace} containing the captured function calls
        @rtype: L{Trace} object
        '''
        self.log.info("Running collection line: exe - %s  arg - %s", exe, arg)
        # Clear the trace recording
        self.trace = []
        if not self.global_limit :
            self.copies = {}
        # Load the application in a debugger
        self.log.info("Loaded program, setting breakpoints")
        self.dbg = pydbg.pydbg()
        self.dbg.load(exe, command_line=arg, create_new_console=True, show_window=False)
        # Set breakpoints on functions
        self.dbg.set_callback(defines.LOAD_DLL_DEBUG_EVENT, self.loadHandler)
        self.dbg.set_callback(defines.USER_CALLBACK_DEBUG_EVENT, self.checkTimeout)
        # Set up the timeout mechanism
        self.timed_out = False
        t = threading.Timer(self.limit, self.timeoutHandler)
          
        self.log.info("Running the program")
        t.start()
        self.dbg.run()
        t.cancel()
        
        self.log.info("Program terminated, recording type information")
        # Record the type information and create the Trace
        if not len(self.trace) == 0 :
            usertypes = {}
            for usernode in self.model.getElementsByTagName("usertype"):
                userid = usernode.getAttribute("id")
                usertype = usernode.getAttribute("type")
                userparams = []
                for childnode in usernode.getElementsByTagName("param") :
                    userparams.append(childnode.getAttribute("type"))
                usertypes[userid] = (usertype, userparams)
            newtrace = trace.Trace(self.trace, usertypes)
        else :
            newtrace = None
            
        # Record some collection stats
        possible = 0
        seen = 0
        for (func, copies) in self.copies.items() :
            possible += 1
            if copies > 0 :
                seen += 1
                self.collected.add(func)
             
        self.log.info("Collected %d unique function calls out of %d collectable functions", seen, possible)
                
        return newtrace
    
    def checkTimeout(self, dbg):
        '''
        Checks for timeouts, in which case it logs the hang and terminates
        the process. This function should be set as the handler for the 
        debugger's event loop (called at least every 100ms)
        
        @param dbg: The debugger that should be used to access memory
        @type dbg: L{pydbg} object
        '''
        if self.timed_out :
            # Terminate the process
            self.log.info("Trace recorder timed out")
            self.log.info("Terminating recorded application")
            dbg.terminate_process() 
            self.timed_out = False
    
    def timeoutHandler(self):
        '''
        Sets the timed_out flag. This function should be automatically
        called after (self.limit) seconds have elapsed since the beginning
        of the currently running program.
        '''
        self.timed_out = True
        self.log.debug("Timeout handler triggered")
        
    def loadHandler(self, dbg):
        '''
        Goes through the functions listed by the xml model and sets breakpoints
        at each function's entry point.
        
        This function should be set as the handler for DLL load events detected
        by the debugger. It sets a breakpoint for each function whose handler
        is designated as the L{funcHandler} function, and the breakpoint
        description is set to the ordinal of the function so L{funcHandler}
        can identify it. Each hooked function is also added to the copies
        table so the number of times it is captured can be recorded.
        
        @param dbg: The debugger that should be used to access memory
        @type dbg: L{pydbg} object
        
        @return: Handler return code from L{defines} module
        @rtype: integer
        '''
        last_dll = dbg.get_system_dll(-1)
        self.log.debug("Caught event loading: %s from %s into: %08x size: %d", \
                       last_dll.name, last_dll.path, last_dll.base, last_dll.size)
        dllname =  os.path.split(self.dllpath)[1]
        if last_dll.name == dllname:
            self.log.info("Setting breakpoints for dll %s", dllname)
            for node in self.model.getElementsByTagName("function") :
                name = str(node.getAttribute("name"))
                address = dbg.func_resolve(last_dll.path, name)
                if address == 0x0 :
                    msg = "Unable to resolve address for %s"
                    self.log.error(msg, name)
                    raise Exception(msg % name)
                self.log.debug("Setting breakpoint: dll %s name %s address %x", dllname, name, address)
                desc = name
                try :
                    dbg.bp_set(address, description=desc, handler=self.funcHandler)
                    self.log.debug("Breakpoint set at address %x", address)
                    if not self.copies.has_key(name) :
                        self.copies[name] = 0
                        self.log.debug("Added %s to copies table", name)
                except :
                    self.log.warning("Couldn't set breakpoint in dll %s at address %x", dllname, address)
                
        return defines.DBG_CONTINUE 
        
    def funcHandler(self, dbg):
        '''
        Activated upon a function call. Determines which function was called
        and checks to see if that function has been recorded before and how
        many times. If the function has been recorded as many times as 
        specified in the config file (collector->copy_limit) the
        snapshot is not captured. Otherwise this function
        starts the snapshot process to capture the function arguments
        using the L{FuncRecorder} object. The created L{Snapshot} is 
        appended to the end of the self.trace list.
        
        @param dbg: The debugger that should be used to access memory
        @type dbg: L{pydbg} object
        
        @return: Handler return code from L{defines} module
        @rtype: integer
        '''
        self.log.debug("Breakpoint tripped, address %x", dbg.context.Eip)
        name = dbg.breakpoints[dbg.context.Eip].description
        num_copies = self.copies[name]
        self.log.debug("Function %s has been captured %d times before", \
                   name, num_copies)
        
        if num_copies < self.copy_limit :
            self.log.info("Recording function call to %s", name)
            snap = self.func_recorder.record(dbg, name)
            self.trace.append(snap)  
            self.copies[name] = num_copies + 1
        else :
            self.log.info("Copy limit reached for function %s, skipping", name)
                
        return defines.DBG_CONTINUE