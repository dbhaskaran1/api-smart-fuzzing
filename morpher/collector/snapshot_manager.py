'''
Created on Oct 26, 2011

@author: Rob
'''

import range_union
import logging
import struct
from morpher.misc import block, memory, tag

class SnapshotManager(object):
    '''
    classdocs
    '''

    def __init__(self, cfg, dbg, ordinal):
        '''
        Constructor takes a cfg object and a pydbg debugger attached to
        the target process
        '''
        # The Config object used for configuration info
        self.cfg = cfg
        # The logging object used for reporting
        self.log = logging.getLogger(__name__)
        # The pydbg object used to read the process memory for the snapshot
        self.dbg = dbg
        # Ordinal of the function we are snapshotting
        self.ordinal = ordinal
        # Set of tags that need to be registered in the snapshot
        self.tset = set()
        # The RangeUnion object used to construct the final list of memory
        # ranges we need to capture for the snapshot
        self.ru = range_union.RangeUnion()
        # The function's argument tags
        self.args = []
        
    def addArg(self, start, fmt):
        '''
        Add a tag (start, fmt) to our list of argument tags
        '''
        self.args.append(tag.Tag(start, fmt))
        
    def checkObject(self, start, fmt):
        '''
        Returns True if the tag (start, fmt) is already in the manager
        '''
        return tag.Tag(start, fmt) in self.tset
        
    def addObjects(self, start, fmt):
        '''
        Adds the memory range from start to start + (size of fmt) -1 to the list
        of areas we need to record for the snapshot and adds a tag for each object
        '''
        curaddr = start
        for c in fmt :
            # Create the tag
            t = tag.Tag(curaddr, c)
            self.tset.add(t)
            curaddr += struct.calcsize(c)
        # Create the range to record
        size = struct.calcsize(fmt)
        r = self.ru.Range(start, start + size - 1)
        self.log.debug("Adding objects type %s, total range from %x to %x to recorder", fmt, r.low, r.high)
        self.ru.add(r)
        self.log.debug("%s", str(self.ru.rlist))
        
    def snapshot(self):
        '''
        Uses the debugger to record the requested areas of the process's memory
        and returns the contents as a Memory object
        '''
        blist = []
        self.log.info("Recording snapshot to file")
        # Record memory blocks
        for r in self.ru.rlist :
            self.log.debug("Recording range from %x to %x", r.low, r.high)
            addr = r.low
            size = r.high - r.low + 1
            data = self.dbg.read_process_memory(addr, size)
            b = block.Block(addr, data)
            blist.append(b)
        # Get function ordinal and arguments address
        self.log.debug("Setting ordinal to %d", self.ordinal)
        self.log.debug("Creating memory object")
        # Create the Memory snapshot and populate it
        m = memory.Memory(self.ordinal, blist)
        m.setArgs(self.args)
        for t in self.tset :
            m.addTag(t)     
        if self.log.isEnabledFor(logging.DEBUG):
            self.log.debug("Returning memory object:")
            self.log.debug(m.toString())
        return m

