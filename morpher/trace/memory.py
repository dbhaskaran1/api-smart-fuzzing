'''
Contains the L{Memory} class for maintaining a collection of L{Blocks}

@author: Rob Waaser
@contact: robwaaser@gmail.com
@organization: Carnegie Mellon University
@since: October 26, 2011
'''
import struct
import block

class Memory(object):
    '''
    Acts as an interface to a collection of L{Block} objects and provides
    methods for patching pointers into those memory segments.
    
    A single L{Memory} object maintains a collection of L{Block} objects
    and serves as a global interface to those blocks that hides the details
    of which block is actually being read to or written from. This class
    is designed to be serialized and deserialized, and provides methods
    that can update pointers after their target objects have been moved to
    new addresses.
    
    Pointers are "registered" by their addresses using the L{registerPointer}
    method. Calling the L{patch} method causes the value of each pointer to 
    be fetched, and the virtual target address to be translated to the real
    address that data now occupies using the L{Block.translate} method.
    
    @note: It is assumed that the underlying L{Block} objects contain
           non-overlapping and non-consecutive ranges of memory
           
    @ivar mem: A dictionary mapping addresses to L{Block} objects
    @ivar pointers: A set containing addresses of pointer objects
    '''
    
    def __init__(self, blklist):
        '''
        Takes a list of (address, data) tuples, where address is a virtual
        address and data is a byte string representing the memory contents
        to store at that address, and adds them to the internal memory map. 
        It is assumed that these blocks contain non-overlapping and 
        non-consecutive ranges of memory
        
        @requires: blklist must consist of disjoint memory ranges
        
        @param blklist: The contents of this L{Memory} as a list of
                        (address, data) pairs
        @type blklist: (integer, byte string) tuple list
        '''
        # Dictionary of address -> char[] 
        self.mem = {}
        # Populate the memory with blocks
        for (addr, data) in blklist :
            b = block.Block(addr, data)
            self.mem[b.addr] = b
        # Set of addresses of pointers
        self.pointers = set()
        
    def __getstate__(self):
        '''
        L{pickle} calls this method when dumping. Turns off all the
        blocks so they can be pickled, then returns this object's
        __dict__ attribute for serialization. 
         
        @note: The blocks will automatically re-activate themselves 
               individually when an operation is performed on them - 
               otherwise L{setActive} can force them all to 
               reactivate right then
               
        @return: This object's __dict__ attribute
        @rtype: dictionary
        '''
        for b in self.mem.values() :
            b.setActive(False)
        return self.__dict__
    
    def __setstate__(self, newdict):
        '''
        Pickle calls this method when unpickling. Restores this object's
        __dict__ from the unserialized version given, then reactivates
        all of the constituent L{Block} objects.
        
        @param newdict: The deserialized __dict__ for this object
        @type newdict: dictionary
        '''
        self.__dict__ = newdict
        for b in self.mem.values() :
            b.setActive(True)
            
    def setActive(self):
        '''
        Utility method to re-enable all L{Block}s in this object
        '''
        for b in self.mem.values() :
            b.setActive(True)
            
    def registerPointer(self, addr):
        '''
        Stores the given address in a set of addresses pointing to 
        pointers in memory, so that the pointer contents can be
        properly updated to preserve their meaning using L{patch}.
        
        @raise Exception: If the range [addr, addr + sizeof(pointer) - 1]
                          is not contained in this memory

        @param addr: The address of the pointer object in this memory
        @type addr: integer
        '''
        size = struct.calcsize("P")
        if not self.containsAddress(addr, size):
            raise Exception("Pointer address is not valid")
        self.pointers.add(addr)
        
    def unregisterPointer(self, addr):
        '''
        Removes an address from the internal pointer registry that was
        previously added using L{registerPointer}.
        
        @param addr: The address of the pointer object in this memory
        @type addr: integer
        '''
        self.pointers.discard(addr)
            
    def read(self, addr, size = None, fmt = None):
        '''
        Reads data from this L{Memory} as either a raw byte
        string or a tuple of objects
        
        Given an address in this L{Memory} and a size in bytes,
        returns 'size' raw bytes present at that address. If
        an optional format of the type specified in the L{struct}
        module is given, the size parameter is ignored and the fmt
        is used to unpack and return the contents as a tuple of objects
        
        @raise Exception: If neither the size nor format is supplied
        @raise Exception: If the given address range is not totally
                          contained by one of the underlying L{Block}s.
        
        @param addr: The virtual address to read from
        @type addr: integer
        
        @param size: The number of bytes to read
        @type size: integer
        
        @param fmt: The format of the object(s) to read
        @type fmt: string
        
        @return: Raw byte string or tuple of objects
        @rtype: byte string or tuple
        '''
        if fmt != None :
            size = struct.calcsize(fmt)
        elif size == None :
            raise Exception("Need some indicator of number of bytes to read")
        blk = self._findBlock(addr, size)
        if blk == None :
            raise Exception("Address %x size %d not a valid address range" % (addr, size))
        return blk.read(addr, size, fmt=fmt)
    
    def write(self, addr, data, fmt=None):
        '''
        Given an address in this L{Memory} and a byte string or
        tuple of objects, updates the memory at that address.
        
        If a L{struct}-style format is given, data is interpreted as a
        tuple of objects that should be first packed into a byte string 
        before being written to memory. If a format is not specified,
        data is interpreted as a raw byte string to be written to memory
        verbatim.
        
        @raise Exception: If the given memory range is totally contained
                          by one of the constituent L{Block}s.
        
        @param addr: The virtual address to write to
        @type addr: integer
        
        @param data: The objects or bytes to write to memory
        @type data: Tuple or byte string
        
        @param fmt: An optional format string
        @type fmt: string
        '''
        if fmt != None:
            size = struct.calcsize(fmt)
        else :
            size = len(data)
        blk = self._findBlock(addr, size)
        if blk == None :
            raise Exception("Address %x size %d not a valid address range" % (addr, size))
        blk.write(addr, data, fmt=fmt)
       
    def patch(self):
        '''
        For each pointer in this L{Memory} whose address is registered,
        this method updates the pointer's value to reflect the ACTUAL address
        of the object it originally pointed to.
        '''
        for addr in self.pointers :
            blk = self._findBlock(addr, struct.calcsize("P"))
            p = blk.read(addr, fmt="P")[0]
            tgtblk = self._findBlock(p, 1)
            # Don't try to translate pointers to memory we don't control
            # EG pointers to kernel memory, NULL pointers
            if tgtblk == None :
                continue
            p = tgtblk.translate(p)
            blk.write(addr, (p,), fmt="P")
            
    def containsAddress(self, addr, size=1):
        '''
        Checks whether the given range is wholly contained in this
        L{Memory} object.
        
        @param addr: The virtual address the range starts at
        @type addr: integer
        
        @param size: The size of the range to check
        @type size: integer
        
        @return: I{True} if the range exists, I{False} otherwise
        @rtype: Boolean
        '''
        return self._findBlock(addr, size) != None
    
    def toString(self):
        '''
        Creates a pretty-printed string containing the contents of this
        L{Memory} in a format suitable for display.
        
        @return: A string representing this object's contents
        @rtype: string
        '''
        memstr = "Contents of Memory:\n"
        memstr += "Pointers: "
        for p in self.pointers : 
            memstr += "0x%x  " % (p)
        memstr += "\n"
        for b in self.mem.values():
            memstr += b.toString() + "\n"
        return memstr
        
    def _findBlock(self, addr, size):
        '''
        Given an address and a size, return the appropriate L{Block} or None 
        if such a range is not covered.
        
        @param addr: The virtual address the range starts at
        @type addr: integer
        
        @param size: The size of the range in question
        @type size: integer
        
        @return: The containing L{Block} or I{None} if it does not exist
        @rtype: L{Block} object or I{None}
        '''
        # Do a quick check if a block with address with key exists
        blk = self.mem.get(addr, None)
        if blk != None and blk.contains(addr, size):
            return blk
        
        # Else search for the correct block
        for blk in self.mem.values() :
            if blk.contains(addr,size) :
                return blk
        return None
