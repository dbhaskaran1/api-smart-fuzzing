'''
Contains the L{Snapshot} class for storing and replaying a function call

@author: Rob Waaser
@contact: robwaaser@gmail.com
@organization: Carnegie Mellon University
@since: November 13, 2011
'''
import memory
import struct
import ctypes
from morpher.trace import typemanager

class Snapshot(object):
    '''
    Contains enough information to replay a captured function call in its
    entirety. 
    
    A L{Memory} object is combined with a set of L{Tag} objects and a 
    L{TypeManager} object to act as snapshot of a function call. The 
    L{Memory} is used to store the actual argument values observed on the 
    stack and the values they point to, while the L{Tag} objects assign
    type information to these recorded values. A supplied L{TypeManager}
    object can then be used to translate this type data into actual classes
    that can be used to instantiate objects and load them with values 
    from the memory capture, which can then be used by the L{ctypes} 
    to replay the originally recorded function call.
    
    @todo: Add the capability to record and replay global variables
    
    @ivar mem: Internal L{Memory} object for storing data
    @ivar tags: Set of L{Tag} objects associating types with data
    @ivar ordinal: The ordinal of the function call that was captured
    @ivar args: Ordered list of L{Tag} objects describing function arguments
    @ivar type_manager: Used to temporarily store a L{TypeManager} used 
                        during a function call
    '''

    def __init__(self, ordinal, blklist):
        '''
        Stores the given function information and the contents of memory
        described as a list of (address, data) tuples, where address is 
        a virtual address and data is a byte string to store at that 
        address. Initially the tag set and argument list are empty.
        
        @requires: blklist must consist of disjoint memory ranges
        
        @param ordinal: The ordinal of the function call captured
        @type ordinal: integer
        
        @param blklist: The contents of this L{Memory} as a list of
                        (address, data) pairs
        @type blklist: (integer, byte string) tuple list
        '''
        # Our internal memory snapshot
        self.mem = memory.Memory(blklist)
        # Set of object tags in our memory
        self.tags = set()
        # Ordinal of the function we recorded
        self.ordinal = ordinal
        # Ordered list of argument tags
        self.args = []
        # Type Manager
        self.type_manager = None

    def setArgs(self, args):
        '''
        Saves an ordered list of argument tags for this function call.
        
        @param args: A list of L{Tag}s describing the function arguments
                     in the same order they were observed
        @type args: L{Tag} object list
        '''
        self.args = args
        
    def addTag(self, tag):
        '''
        Adds the given L{Tag} object to the internal tag set
        
        @raise Exception: If the tag's address is not valid for this object
        
        @param tag: The tag object to register
        @type tag: L{Tag} object
        '''
        size = struct.calcsize(tag.fmt)
        if not self.mem.containsAddress(tag.addr, size) : 
            raise Exception("Address %x size %d not a valid address range" % (tag.addr, size))
        self.tags.add(tag)
        if tag.fmt == "P" :
            self.mem.registerPointer(tag.addr)
        
    def removeTag(self, tag):
        '''
        Removes a L{Tag} object previously given to L{addTag}
        
        @param tag: The tag object to remove
        @type tag: L{Tag} object
        '''
        self.tags.remove(tag)
        if tag.fmt == "P" :
            self.mem.unregisterPointer(tag.addr)
        
    def replay(self, typeman):
        '''
        Patches internal pointers and extracts a list of argument objects
        observed for this captured function call.
        
        Any registered pointers are changed so they point to the actual
        addresses of the objects they originally referred to. The supplied
        L{TypeManager} object is then used to construct L{ctypes} classes
        that represent the equivalent C types for each object that was
        captured as an argument to this function call. The stored argument
        values are then used to create equivalent objects from the L{ctypes}
        classes and returned in an ordered list, which can be used in a
        call to the same function loaded using L{ctypes}.
        
        @param typeman: A L{TypeManager} object used to interpret format
                        strings used to tag objects in this L{Snapshot}
        @type typeman: L{TypeManager} object
        '''
        self.type_manager = typeman
        self.mem.patch()
        arguments = []
        for tag in self.args :
            arg = self._loadObject(tag.addr, tag.fmt)
            arguments.append(arg)
        self.type_manager = None
        return arguments
    
    def toString(self):
        '''
        Creates a pretty-printed string containing the contents of this
        L{Snapshot} in a format suitable for display.
        
        @return: A string representing this object's contents
        @rtype: string
        '''
        snapstr = "Snapshot Contents:\n"
        snapstr += "Ordinal: %d\n" % self.ordinal
        if len(self.args) == 0 :
            snapstr += "Arguments not specified\n" 
        else :
            snapstr += "Argument Tags: "
            for t in self.args : 
                snapstr += "0x%x - %s   " % (t.addr, t.fmt)
            snapstr += "\nArguments: "
            self.type_manager = typemanager.TypeManager()
            for t in self.args :
                if not t.fmt.isdigit() :
                    a = self._loadObject(t.addr, t.fmt)
                    try :
                        s = str(a)
                        snapstr += s + " "
                    except :
                        snapstr += "(unprintable) "
                else :
                    snapstr += "UserType(%s) " % t.fmt
            snapstr += "\n"
            self.type_manager = None
        snapstr += "Tags: "
        for t in self.tags : 
            snapstr += "0x%x - %s   " % (t.addr, t.fmt)
        snapstr += "\n" + self.mem.toString()
        return snapstr
        
    def _loadObject(self, addr, fmt, objclass=None):
        '''
        Recursive function used to load contents of memory contained
        in this L{Snapshot} into an instance of a corresponding 
        L{ctypes} class. Uses the classes and information returned by 
        the stored L{TypeManager} object type_manager to reconstruct
        user types such as Structures and Unions and properly populate
        their fields, even in the case of recursive structures.
        
        @param addr: The address of the object to load
        @type addr: integer
        
        @param fmt: The format string corresponding to the type to load
        @type fmt: string
        
        @param objclass: The corresponding L{ctypes} class for the fmt
                         string as provided by the L{TypeManager}, if
                         available
        @type objclass: L{ctypes} class
        
        @return: Instance of fmt's corresponding class loaded with value
                 from the specified memory address
        @rtype: L{ctypes} object
        '''
        # Need the object class, so if its not given look it up
        if objclass == None :
            objclass = self.type_manager.getClass(fmt)
        if issubclass(objclass, ctypes.Structure) :
            # This is a structure, recursively populate each field
            offset = 0
            myinst = objclass()
            for (fieldname, fieldclass) in objclass._fields_ :
                # Get size and alignment information
                fieldfmt = self.type_manager.getFormat(fieldclass)
                (size, alignment) = self.type_manager.getInfo(fieldfmt)
                # Move to correctly aligned address
                offset = self.type_manager.align(offset, alignment)
                # Load the object for this field
                obj = self._loadObject(addr + offset, fieldfmt, fieldclass)
                # Store the object as this field's value
                setattr(myinst, fieldname, obj)
                offset += size
            return myinst
        elif issubclass(objclass, ctypes.Union) :
            # This is a Union, just load the largest field
            myinst = objclass()
            maxsize = 0
            maxfieldname = None
            maxfieldclass = None
            maxfieldfmt = None
            for (fieldname, fieldclass) in objclass._fields_ :
                # Get the size information for this field's type
                fieldfmt = self.type_manager.getFormat(fieldclass)
                (size, _) = self.type_manager.getInfo(fieldfmt)
                # Update the maximum-sized field entry
                if size > maxsize :
                    maxsize = size
                    maxfieldname = fieldname
                    maxfieldclass = fieldclass
                    maxfieldfmt = fieldfmt
            # Load the largest field's object
            obj = self._loadObject(addr, maxfieldfmt, maxfieldclass)
            # Store the object as that field's value
            setattr(myinst, maxfieldname, obj)
            return myinst
        else :
            # This is a standard ctype format, read the object directly
            v = self.mem.read(addr, fmt=fmt)[0] 
            return objclass(v)
