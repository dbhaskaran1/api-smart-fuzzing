'''
Contains the L{FuncRecorder} class for recording a L{Snapshot} 
of a function call

@author: Rob Waaser
@contact: robwaaser@gmail.com
@organization: Carnegie Mellon University
@since: November 14, 2011
'''

import logging
import struct
import snapshot_manager
from morpher.pydbg import pdx
from morpher.trace import typemanager

class FuncRecorder(object):
    '''
    Used to capture the state of a function call using a supplied debugger.
    
    The L{FuncRecorder} class contains enough information to be able to
    interpret and traverse the stack of another process, captured at the
    moment of a function call, and pinpoint areas of the stack that need 
    to be captured and recorded in order to reproduce the function call
    at a later date. The tagging process used by the L{FuncRecorder} is
    designed to minimize the amount of memory that is copied for the 
    capture, while handling complex cases such as structures/unions and
    capturing the content referenced by pointers. The end goal is to
    produce a L{Snapshot} object that reproduces the exact same function
    call and contains all the available information about the types
    of the objects captured (so they can be intelligently fuzzed).
    
    @ivar cfg: The L{Config} object
    @ivar log: The L{logging} object
    @ivar model: The XML root L{Node} for the DLL model
    @ivar stack_align: The alignment requirement for the stack
    @ivar type_manager: The L{TypeManager} used for type information 
    @ivar dbg: The L{pydbg} debugger
    @ivar sm: L{SnapshotManager} object for creating image
    '''

    def __init__(self, cfg, model):
        '''
        Stores the given config object for local configuration
        information and initializes the instance variables. The 
        local type manager is initialized using the supplied model
        data, which is also used to traverse the stack of the 
        function being recorded.
        
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
        # Stack alignment
        self.stack_align = self.cfg.getint('collector', 'stack_align')
        
        # Gather custom type information for the type manager
        usertypes = {}
        for usernode in model.getElementsByTagName("usertype"):
            userid = usernode.getAttribute("id")
            usertype = usernode.getAttribute("type")
            userparams = []
            for childnode in usernode.getElementsByTagName("param") :
                userparams.append(childnode.getAttribute("type"))
            usertypes[userid] = (usertype, userparams)
            
        # Type interpreter  
        self.type_manager = typemanager.TypeManager(usertypes)
        # Debugger
        self.dbg = None
        # Snapshot manager
        self.sm = None
    
    def record(self, dbg, name):
        '''
        Activated upon a function call and used to record the stack. 
        
        Should be called when the target process is paused by a debugger at
        the beginning of a function call. Uses the supplied debugger object 
        to start the snapshot process and accesses the target process's 
        memory space to capture the function arguments. 
        
        @param dbg: The debugger that should be used to access memory
        @type dbg: L{pydbg} object
        
        @param name: The name of the function we are recording
        @type name: string
        
        @return: The filled snapshot containing the image of this function call
        @rtype: L{Snapshot} object
        '''
        self.dbg = dbg
        startaddr = self.dbg.context.Esp + 0x4
        # Figure out what function this is
        for node in self.model.getElementsByTagName("function") :
            if name == node.getAttribute("name") :
                func = node
                break
        # Create the snapshot manager
        self.sm = snapshot_manager.SnapshotManager(self.cfg, self.dbg, name)
        # Tag arguments
        self.tagArgs(startaddr, func)        
        # Create the snapshot
        snap = self.sm.snapshot()
        
        return snap
    
    def tagArgs(self, addr, funcnode):
        '''
        Starts the recursive tag process for this function's args.
        
        Given the function XML's model and the address of the arguments,
        walks through the arguments and tags each one using this object's
        snapshot manager. 
        
        @note: We can't rely on the arguments being properly aligned - 
               they only need to be aligned to the stack requirements.
               
        @param addr: Address the function arguments start at on the stack
        @type addr: integer
        
        @param funcnode: XML L{Node} for the function
        @type funcnode: L{Node} object
        '''
        curaddr = addr
        for param in funcnode.getElementsByTagName("param") :
            paramtype = param.getAttribute("type")
            (size, _) = self.type_manager.getInfo(paramtype)
            curaddr = self.type_manager.align(curaddr, self.stack_align)
            self.tag(curaddr, paramtype)
            if paramtype.isdigit() :
                self.sm.addArg(curaddr, paramtype)
            else :
                self.sm.addArg(curaddr, paramtype[0])
            curaddr += size
    
    def tag(self, addr, paramtype):
        '''
        Given an address and a type. either basic (ex. "i") or user-defined 
        (ex. "1"), tag the object for collection and recursively tag any 
        member objects or objects it points to.
        
        If the type is user-defined (for example, "1" indicates a user-defined
        type such as a struct), the type's definition is looked up using the
        model and the fields of the type are individually tagged. If the type
        is a basic type, the type is tagged. If the type is a pointer type,
        such as "PPI", a pointer tag ("P") is added and the tagging is 
        recursively performed on the type pointed to ("PI") at the address
        contained in the pointer type.
        
        @note: The tagging algorithm is designed to only record a tag once,
               and handle pointer loops, pointers to the same object but as
               different types, and other complications.
        
        @param addr: The address of the object to tag
        @type addr: integer
        
        @param paramtype: The format string representing the object's type
        @type paramtype: string
        '''
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
            if not self.sm.checkObject(addr, basictype) :
                (size, _) = self.type_manager.getInfo(basictype)
                self.sm.addObject(addr, size, basictype)
            # If it's a pointer follow it even if it's already been added -
            # the type it points to could be different. Don't follow if
            # its just "P" (a void * pointer)
            if paramtype[0] == "P" and len(paramtype) > 1:
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
                    return
                # Tag the pointed-to object
                self.tag(paddr, ptype)