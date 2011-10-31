'''
Created on Oct 28, 2011

@author: Rob
'''
import os
from morpher.collector import snapshot_manager
from morpher.pydbg import pydbg, defines
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
        self.log = cfg.getLogger(__name__)
        # The xml model used for traversal
        self.model = model
        # The target dll
        self.dllpath = self.cfg.get('fuzzer', 'target')
        # The trace
        self.trace = []
    
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
        dbg = pydbg.pydbg()
        dbg.load(exe, command_line=arg)
        # Set breakpoints on functions
        dbg.set_callback(defines.LOAD_DLL_DEBUG_EVENT, self.load_handler)
          
        self.log.info("Running the program")
        dbg.run()
        
        return self.trace
        
    def load_handler(self,dbg):
        '''
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
                dbg.bp_set(address, description=desc, handler=self.func_handler)
                self.log.debug("Breakpoint set at address %x", address)
        
        return defines.DBG_CONTINUE     # or other continue status
        
    def func_handler(self,dbg):
        '''
        '''
        self.log.debug("Breakpoint tripped, address %x", dbg.context.Eip)
        ordinal = int(dbg.breakpoints[dbg.context.Eip].description)
        addr = dbg.context.Esp + 0x4
        # Create the snapshot manager
        sm = snapshot_manager.SnapshotManager(self.cfg, dbg, ordinal, "II")
        # Populate the snapshot with memory objects to record
        sm.addObjects(addr, "II")
        # Take the snapshot
        self.trace.append(sm.snapshot())          
        
        return defines.DBG_CONTINUE 