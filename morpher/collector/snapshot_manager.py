'''
Created on Oct 26, 2011

@author: Rob
'''

import range_union
import pickle
from morpher.misc import block, memory

class SnapshotManager(object):
    '''
    classdocs
    '''

    def __init__(self, cfg, dbg, oridinal, fmt):
        '''
        Constructor takes a cfg object and a pydbg debugger attached to
        the target process
        '''
        # The Config object used for configuration info
        self.cfg = cfg
        # The logging object used for reporting
        self.log = cfg.getLogger(__name__)
        # The pydbg object used to read the process memory for the snapshot
        self.dbg = dbg
        # Set of pointers that need to be registered int he snapshot
        self.pset = set()
        # The RangeUnion object used to construct the final list of memory
        # ranges we need to capture for the snapshot
        self.ru = range_union.RangeUnion()
        # The function's format
        self.fmt = fmt
        
    def add(self, start, size):
        '''
        Adds the memory range from start to start + size -1 to the list
        of areas we need to record for the snapshot
        '''
        r = self.ru.Range
        r.low = start
        r.high = start + size -1
        self.log.debug("Adding range from %p to %p to recorder", r.low, r.high)
        self.ru.add(r)
        self.log.debug("%s", str(self.ru.rlist))
        
    def registerPointer(self, p):
        '''
        Add pointer address to list of pointers that need to be registered
        '''
        self.pset.add(p)
        
    def snapshot(self, f):
        '''
        Uses the debugger to record the requested areas of the process's memory
        and stores the contents as a pickled Memory object
        '''
        blist = []
        self.info("Recording snapshot to file")
        # Record memory blocks
        for r in self.ru.rlist :
            self.log.debug("Recording range from %p to %p", r.low, r.high)
            addr = r.low
            size = r.high - r.low + 1
            data = self.dbg.read_process_memory(addr, size)
            b = block.Block(addr, data)
            blist.append(b)
        # Get function ordinal and arguments address
        ordinal = int(self.dbg.breakpoints[self.dbg.context.Eip].description)
        argaddr = self.dbg.context.Esp
        fmt = self.fmt
        self.log.debug("Setting ordinal to %d, esp to %p, argfmt to %s", ordinal, argaddr, fmt)
        self.log.debug("Creating memory object")
        # Create the Memory snapshot and populate it
        m = memory.Memory(ordinal, blist)
        m.setArgs(argaddr, fmt)
        for p in self.pset :
            m.registerPointer(p)
        self.log.debug("Pickling memory object to file")
        pickle.dump(m, f)
