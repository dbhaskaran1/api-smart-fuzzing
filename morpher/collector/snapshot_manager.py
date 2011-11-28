'''
Contains the L{SnapshotManager} class for creating a L{Snapshot}

@author: Rob Waaser
@contact: robwaaser@gmail.com
@organization: Carnegie Mellon University
@since: October 26, 2011
'''

import range_union
import logging
from morpher.trace import snapshot, tag
from morpher.pydbg import pdx

class SnapshotManager(object):
    '''
    Designed to simplify the process of properly creating a L{Snapshot}
    object. 
    
    The L{SnapshotManager} provides a simple interface consisting
    of functions like L{addArg} and L{addObject} and handles the more complex
    issues in the background, such as using sets to ensure the uniqueness of
    L{Tag}s added to the L{Snapshot} and L{RangeUnion} objects to ensure that
    the minimal amount of memory is copied for the L{Snapshot}. The contents
    of the target process memory are not copied until the L{snapshot} method 
    is called, which uses all the information accumulated to record areas of
    memory using the debugger and create the requested L{Snapshot}
    
    @ivar cfg: The L{Config} object
    @ivar log: The L{logging} object
    @ivar dbg: The L{pydbg} debugger for capturing memory
    @ivar name: Name of the function we are recording
    @ivar tset: The set of L{Tag} objects for this capture
    @ivar ru: L{RangeUnion} object used for ensuring that the minimum necessary 
              amount of process memory is captured
    @ivar args: Ordered list of L{Tag}s corresponding to the function arguments
    '''

    def __init__(self, cfg, dbg, name):
        '''
        Stores the configuration object, a pydbg debugger attached to
        the target process, and the name of the function being captured.
        
        @param cfg: The configuration object to use
        @type cfg: L{Config} object
        
        @param dbg: The debugger used to access the target process
        @type dbg: L{pydbg} object
        
        @param name: The name of the function being called
        @type name: string
        '''
        # The Config object used for configuration info
        self.cfg = cfg
        # The logging object used for reporting
        self.log = logging.getLogger(__name__)
        # The pydbg object used to read the process memory for the snapshot
        self.dbg = dbg
        # Name of the function we are snapshotting
        self.name = name
        # Set of tags that need to be registered in the snapshot
        self.tset = set()
        # The RangeUnion object used to construct the final list of memory
        # ranges we need to capture for the snapshot
        self.ru = range_union.RangeUnion()
        # The function's argument tags
        self.args = []
        
    def addArg(self, addr, fmt):
        '''
        Add a tag (start, fmt) to our list of argument tags
        
        @param addr: Address of the argument being added
        @type addr: integer
        
        @param fmt: Format string representing the argument type
        @type fmt: string
        '''
        self.args.append(tag.Tag(addr, str(fmt)))
        
    def checkObject(self, addr, fmt):
        '''
        Returns True if the tag (addr, fmt) is already in the manager
        
        @param addr: Address of the object being checked
        @type addr: integer
        
        @param fmt: Format string representing the object type
        @type fmt: string
        
        @return: I{True} if tag already registered, I{False} otherwise
        @rtype: Boolean
        '''
        return tag.Tag(addr, str(fmt)) in self.tset
        
    def addObject(self, start, size, fmt):
        '''
        Adds the memory range from start to start + (size of fmt) -1 to the 
        list of areas to capture. A (start, fmt) tag is added for the object.
        
        @param start: Address of the object being added
        @type start: integer
        
        @param size: Size of the object being added
        @type size: integer
        
        @param fmt: Format string representing the object type
        @type fmt: string
        '''
        # Create and add the tag
        t = tag.Tag(start, str(fmt))
        self.tset.add(t)
        # Create the range to record
        r = self.ru.Range(start, start + size - 1)
        self.log.debug("Adding objects type %s, total range from %x to %x to recorder", str(fmt), r.low, r.high)
        self.ru.add(r)
        self.log.debug("%s", str(self.ru.rlist))
        
    def snapshot(self):
        '''
        Uses the debugger to record the requested areas of the process's memory
        and returns the contents as a new L{Snapshot} object. The L{Snapshot}
        is populated using the tags registered using L{addObject} and the 
        arguments added using L{addArg}.
        
        @return: The newly created L{Snapshot}
        @rtype: L{Snapshot} object
        '''
        blist = []
        self.log.info("Recording snapshot to file")
        # Record memory blocks
        for r in self.ru.rlist :
            self.log.debug("Recording range from %x to %x", r.low, r.high)
            addr = r.low
            size = r.high - r.low + 1
            try :
                data = self.dbg.read_process_memory(addr, size)
            except pdx.pdx :
                # Bad pointers shouldn't have gotten to this point
                self.log.error("Error trying to access memory for range %x to %x", r.low, r.high)
                continue
            blist.append((addr, data))
        # Get function ordinal and arguments address
        self.log.debug("Setting name to %s", self.name)
        self.log.debug("Creating memory object")
        # Create the Snapshot and populate it
        s = snapshot.Snapshot(self.name, blist)
        s.setArgs(self.args)
        for t in self.tset :
            if not t.fmt.isdigit() :
                s.addTag(t)     
        if self.log.isEnabledFor(logging.DEBUG):
            self.log.debug("Returning memory object:\n\n%s\n", s.toString())
        return s

