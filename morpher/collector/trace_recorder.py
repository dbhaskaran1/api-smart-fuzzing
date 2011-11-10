'''
Created on Oct 28, 2011

@author: Rob
'''
import os
from morpher.collector import snapshot_manager
from morpher.pydbg import pydbg, defines
import logging
import struct

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
        # Stack alignment
        self.stack_align = self.cfg.getint('collector', 'stack_align')
    
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
        self.dbg.set_callback(defines.LOAD_DLL_DEBUG_EVENT, self.load_handler)
          
        self.log.info("Running the program")
        self.dbg.run()
        
        return self.trace
        
    def load_handler(self,dbg):
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
                dbg.bp_set(address, description=desc, handler=self.func_handler)
                self.log.debug("Breakpoint set at address %x", address)
        
        return defines.DBG_CONTINUE 
        
    def func_handler(self,dbg):
        '''
        Activated upon a function call. Determines which function was called
        and starts the snapshot process to capture the function arguments
        '''
        self.log.debug("Breakpoint tripped, address %x", dbg.context.Eip)
        ordinal = int(dbg.breakpoints[dbg.context.Eip].description)
        startaddr = dbg.context.Esp + 0x4
        # Figure out what function this is
        for node in self.model.getElementsByTagName("function") :
            if ordinal == int(node.getAttribute("ordinal")) :
                func = node
                break
        print "Stopped at stack address %x"  % dbg.context.Esp
        # Create the snapshot manager
        self.sm = snapshot_manager.SnapshotManager(self.cfg, dbg, ordinal)
        # Tag arguments
        self.tagArgs(startaddr, func)
        # Take the snapshot
        self.trace.append(self.sm.snapshot())          
        
        return defines.DBG_CONTINUE 
    
    def tagArgs(self, addr, funcnode):
        '''
        Given the starting address and function node, tag the arguments.
        Note that we can't rely on arguments to be properly aligned - 
        just aligned to the stack requirements.
        '''
        curaddr = addr
        for param in funcnode.getElementsByTagName("param") :
            paramtype = param.getAttribute("type")
            (size, _) = self.getInfo(paramtype)
            curaddr = self.align(curaddr, self.stack_align)
            print "Calling tag on argument of type %s address %x" % (paramtype, curaddr)
            self.tag(curaddr, paramtype)
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
                    (size, alignment) = self.getInfo(childtype)
                    offset = self.align(offset, alignment)
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
                self.sm.addObjects(addr, basictype)
            # If it's a pointer follow it even if it's already been added -
            # the type it points to could be different
            print "len of type %d" % len(paramtype)
            if paramtype[0] == "P" and len(paramtype) > 1:
                print "Recusring"
                # Get the pointer's type (everything after the first P)
                ptype = paramtype[1:]
                # Read the pointer's value (address of object)
                size = struct.calcsize("P")
                raw = self.dbg.read_process_memory(addr, size)
                paddr = struct.unpack("P", raw)[0]
                # Check if this paddr is to valid user memory
                print "Pointer value: %x" % paddr 
                print "Test %s" % (0x28fef8 >= 0x80000000)
                if paddr == 0 or paddr >= 0x80000000:
                    # NULL pointer or pointer to kernel memory, can't collect
                    print "can't collect: paddr = 0 %s" % (paddr >=0x80000000)
                    return
                # Tag the pointed-to object
                self.tag(paddr, ptype)
    
    def getInfo(self, paramtype):
        '''
        Given a fundamental type (ex. "P") or user type (ex. "1"), returns a tuple consisting
        of the (size, alignment) of that type
        '''
        if paramtype.isdigit() :
            # This is a structure or union - get the corresponding node
            for typenode in self.model.getElementsByTagName("usertype"):
                if int(typenode.getAttribute("id")) == int(paramtype) :
                    usernode = typenode
                    break
            if usernode.getAttribute("type") == "struct" :
                # Structs have the same alignment as the largest member alignment.
                # Members are padded so they are at the correct alignments as well
                # Struct end is padded so it falls on the same alignment as struct
                maxalign = 1
                offset = 0
                for child in usernode.getElementsByTagName("param") :
                    (size, alignment) = self.getInfo(child.getAttribute("type"))
                    if alignment > maxalign :
                        maxalign = alignment
                    # Insert padding to achieve member alignment
                    offset = self.align(offset, alignment)
                    # Add actual size of member
                    offset += size;
                # Insert end padding to match structure alignment 
                offset = self.align(offset, maxalign)
                return (offset, maxalign)
            else :
                # Unions have size equal to the size of their largest member, 
                # and alignment equal to the largest member alignment
                maxalign = 1
                maxsize = 1
                for child in usernode.getElementsByTagName("param") :
                    (size, alignment) = self.getInfo(child.getAttribute("type"))
                    if alignment > maxalign :
                        maxalign = alignment
                    if size > maxsize :
                        maxsize = size
                return (maxalign, maxsize)
        else :
            # This is a standard type. Alignment is equal to type's size
            size = struct.calcsize(paramtype[0])
            alignment = size
            return (size, alignment)
        
    def align(self, address, alignment):
        '''
        Utility function to align an address by adding padding
        '''
        leftover = (address % alignment)
        padding = (alignment - leftover) % alignment
        return address + padding