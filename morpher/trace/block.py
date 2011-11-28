'''
Contains the L{Block} class definition for maintaining a piece of memory

@author: Rob Waaser
@contact: robwaaser@gmail.com
@organization: Carnegie Mellon University
@since: October 26, 2011
'''

import ctypes
import struct

class Block(object):
    '''
    Encapsulates a memory block and provides an interface for 
    reading/writing that memory. 
    
    The memory block is represented as a byte string, and is stored along
    with the "virtual address" that the memory block starts at. Reads and
    writes use these virtual addresses and the L{struct} module to access
    the contents of the byte string. The class is maintained in such a 
    way that it can be serialized and deserialized using the I{pickle}
    module, and provides a L{translate} method that can take a virtual
    address and return the actual address the bytestring currently occupies.
    
    @ivar size: The length of the stored byte string
    @ivar addr: The virtual address the byte string starts at
    @ivar data: The stored byte string
    @ivar active: Boolean indicating if the byte array is in a serializable 
                  state (I{False}) or not (I{True})
    '''

    def __init__(self, addr, data):
        '''
        Stores an array of raw bytes along with the virtual address it starts
        at. The byte string is originally stored as a ctypes string buffer,
        which allows us to retrieve the actual raw address of the byte string.
        
        @param addr: The virtual address of the beginning of the data
        @type addr: integer
        
        @param data: The byte string to store
        @type data: byte string
        '''
        # The size of this block in bytes
        self.size = len(data)
        # The starting address of the memory captured in this block
        self.addr = addr
        # When active, a ctypes string buffer; inactive, a bytearray
        self.data = ctypes.create_string_buffer(data)
        # Flag indicating if we are active(can be accessed by address)
        # or inactive (in a mode allowing pickling) (pickling will not
        # work on a ctypes pointer object)
        self.active = True
        
    def setActive(self, flag):
        '''
        Converts the internal byte string to and from a serializable string.
        
        Blocks can't be pickled if they contain ctypes pointers, so
        this method "turns off" the block and converts the data to
        a pickle-friendly string if the flag is I{False}, and the
        reverse if the flag is I{True}.
        
        @param flag: The state the block should be set to
        @type flag: Boolean
        '''
        if flag == self.active:
            return
        if flag == True:
            self.data = ctypes.create_string_buffer(self.data)
            self.active = True
        else :
            self.data = self.data.raw[:self.size]
            self.active = False
            
        
    def read(self, addr, size = None, fmt = None):
        '''
        Reads data from this L{Block} as either a raw byte
        string or a tuple of objects
        
        Given an address in this L{Block} and a size in bytes,
        returns 'size' raw bytes present at that address. If
        an optional format of the type specified in the L{struct}
        module is given, the size parameter is ignored and the fmt
        is used to unpack and return the contents as a tuple of objects
        
        @raise Exception: If neither the size nor format is supplied
        
        @param addr: The virtual address to read from
        @type addr: integer
        
        @param size: The number of bytes to read
        @type size: integer
        
        @param fmt: The format of the object(s) to read
        @type fmt: string
        
        @return: Raw byte string or tuple of objects
        @rtype: byte string or tuple
        '''
        if not self.active :
            self.setActive(True)
        if fmt != None :
            size = struct.calcsize(fmt)
        elif size == None :
            raise Exception("Need some indicator of number of bytes to read")
        buf = ctypes.create_string_buffer(size)
        real_addr = self.translate(addr)
        ctypes.memmove(buf, real_addr, size)
        if fmt == None :
            ret = buf.raw
        else :
            ret = struct.unpack(fmt, buf.raw)
        return ret
    
    def write(self, addr, data, fmt=None):
        '''
        Given an address in this L{Block} and a byte string or
        tuple of objects, updates the memory at that address.
        
        If a L{struct}-style format is given, data is interpreted as a
        tuple of objects that should be first packed into a byte string 
        before being written to memory. If a format is not specified,
        data is interpreted as a raw byte string to be written to memory
        verbatim.
        
        @param addr: The virtual address to write to
        @type addr: integer
        
        @param data: The objects or bytes to write to memory
        @type data: Tuple or byte string
        
        @param fmt: An optional format string
        @type fmt: string
        '''
        if not self.active :
            self.setActive(True)
        if fmt != None:
            data = struct.pack(fmt, *data)
        buf = ctypes.c_char_p(data)
        size = len(data)
        real_addr = self.translate(addr)
        ctypes.memmove(real_addr, buf, size)
        
    def contains(self, addr, size):
        '''
        Returns True if range [addr, addr + size - 1] is contained
        in this block.
        
        @param addr: The starting address of the range in question
        @type addr: integer
        
        @param size: The size of the range in question
        @type size: integer
        
        @return: True if the range is entirely contained by this L{Block},
                 False otherwise.
        @rtype: Boolean
        '''
        return addr >= self.addr and addr + size <= self.addr + self.size
        
    def translate(self, addr):
        '''
        Given a virtual address in the captured block's memory space, 
        returns the actual address in memory of the data pointed to 
        by the virtual address.
        
        @param addr: The virtual address to translate
        @type addr: integer
        
        @return: The real address corresponding to the given virtual address
        @rtype: integer
        '''
        if not self.active :
            self.setActive(True)
        # Null stays as Null!
        if addr == 0 :
            return 0
        offset = addr - self.addr
        return ctypes.addressof(self.data) + offset

    def toString(self):
        '''
        Creates a pretty-printed string containing the contents of this
        L{Block} in a format suitable for display.
        
        @return: A string representing this object's contents
        @rtype: string
        '''
        if not self.active :
            self.setActive(True)
        blkstr = "Block - Size: %d, Address: 0x%x, Contents: " % (self.size, self.addr)
        for i in range(self.size) :
            if i % 4 == 0 :
                blkstr += " "
            blkstr += "\\x%02x" % ord(self.data.raw[i])
        return blkstr