'''
Created on Nov 14, 2011

@author: Rob
'''
import logging
import struct
import snapshot_manager
from morpher.pydbg import pdx
from morpher.trace import typemanager

class FuncRecorder(object):
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
        # Stack alignment
        self.stack_align = self.cfg.getint('collector', 'stack_align')
        # Type interpreter
        self.type_manager = typemanager.TypeManager(model)
        # Debugger
        self.dbg = None
    
    def record(self, dbg, ordinal):
        '''
        Activated upon a function call. Determines which function was called
        and starts the snapshot process to capture the function arguments
        '''
        self.dbg = dbg
        startaddr = self.dbg.context.Esp + 0x4
        # Figure out what function this is
        for node in self.model.getElementsByTagName("function") :
            if ordinal == int(node.getAttribute("ordinal")) :
                func = node
                break
        print "Stopped at stack address %x"  % self.dbg.context.Esp
        # Create the snapshot manager
        self.sm = snapshot_manager.SnapshotManager(self.cfg, self.dbg, ordinal)
        # Tag arguments
        self.tagArgs(startaddr, func)        
        # Create the snapshot
        snap = self.sm.snapshot()
        
        return snap
    
    def tagArgs(self, addr, funcnode):
        '''
        Given the starting address and function node, tag the arguments.
        Note that we can't rely on arguments to be properly aligned - 
        just aligned to the stack requirements.
        '''
        curaddr = addr
        for param in funcnode.getElementsByTagName("param") :
            paramtype = param.getAttribute("type")
            (size, _) = self.type_manager.getInfo(paramtype)
            curaddr = self.type_manager.align(curaddr, self.stack_align)
            print "Calling tag on argument of type %s address %x" % (paramtype, curaddr)
            self.tag(curaddr, paramtype)
            if paramtype.isdigit() :
                print "adding arg tag of type %s address %x" % (paramtype, curaddr)
                self.sm.addArg(curaddr, paramtype)
            else :
                print "adding arg tag of type %s address %x" % (paramtype[0], curaddr)
                self.sm.addArg(curaddr, paramtype[0])
            curaddr += size
    
    def tag(self, addr, paramtype):
        '''
        Given an address and a type. either basic (ex. "i") or user-defined (ex. "1"),
        tag the object for collection and recursively tag any member objects or 
        objects it points to
        '''
        print "tag called with addr %x type %s" % (addr, paramtype)
        # Check the node type
        if paramtype.isdigit() :
            if not self.sm.checkObject(addr, paramtype) :
                (size, _) = self.type_manager.getInfo(paramtype)
                self.sm.addObject(addr, size, paramtype)
                # This is a user-defined type - get definition node
                for typenode in self.model.getElementsByTagName("usertype"):
                    if int(typenode.getAttribute("id")) == int(paramtype) :
                        usernode = typenode
                        break
                # Check if this is a struct or union type
                if usernode.getAttribute("type") == "struct" :
                    # Struct type. Use alignment on offset, not address - we know
                    # structure will be internally aligned, but can't guarantee
                    # it's stack address is aligned properly
                    offset = 0
                    for childnode in usernode.getElementsByTagName("param") :
                        childtype = childnode.getAttribute("type")
                        (size, alignment) = self.type_manager.getInfo(childtype)
                        offset = self.type_manager.align(offset, alignment)
                        self.tag(addr + offset, childtype)
                        offset += size
                else :
                    # Union type - tag all elements with same address
                    for childnode in usernode.getElementsByTagName("param") :
                        self.tag(addr, childnode.getAttribute("type"))
                
        else :
            # This is a basic type - add it if tag does not already exist
            basictype = paramtype[0]
            print "basictype = %s" % basictype
            if not self.sm.checkObject(addr, basictype) :
                (size, _) = self.type_manager.getInfo(basictype)
                self.sm.addObject(addr, size, basictype)
            # If it's a pointer follow it even if it's already been added -
            # the type it points to could be different. Don't follow if
            # its just "P" (a void * pointer)
            print "len of type %d" % len(paramtype)
            if paramtype[0] == "P" and len(paramtype) > 1:
                print "Recursing"
                # Get the pointer's type (everything after the first P)
                ptype = paramtype[1:]
                # Read the pointer's value (address of object)
                try :
                    size = struct.calcsize("P")
                    raw = self.dbg.read_process_memory(addr, size)
                    paddr = struct.unpack("P", raw)[0]
                except pdx.pdx :
                    # Shouldn't have gotten here, someone gave bad argument
                    # This is a bad object, not in valid memory
                    # We'll discard it during the snapshot
                    return
                # Check if this paddr is to valid user memory
                (size, _) = self.type_manager.getInfo(ptype)
                try : 
                    self.dbg.read_process_memory(paddr, size)
                except pdx.pdx :
                    print "can't collect: paddr = %x" % (paddr)
                    return
                # Tag the pointed-to object
                self.tag(paddr, ptype)