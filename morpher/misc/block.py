'''
Created on Oct 26, 2011

@author: Rob
'''

import ctypes
import struct

class Block(object):
    '''
    classdocs
    '''

    def __init__(self, addr, data):
        '''
        Parameters are an address and array of raw bytes
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
        Blocks can't be pickled if they contain ctypes pointers. So
        this method "turns off" the block and converts the data to
        a pickle-friendly string, and back again
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
        Given an address in this Block and a size in bytes,
        returns 'size' raw bytes present at that address. If
        an optional format of the type specified in the struct
        module is given, the size parameter is ignored and the fmt
        is used to unpack and return the contents as a tuple of objects
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
        Given an address in this Block and an array of raw bytes,
        updates the memory at that address in this Block. If a
        struct-style format is given, data is interpreted as a
        tuple of objects that should be first packed into 
        a byte string before being written to memory
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
        Return True if range (addr, addr + size -1) is contained
        in this block
        '''
        return addr >= self.addr and addr + size <= self.addr + self.size
        
    def translate(self, addr):
        '''
        Given an address in the captured block's memory space, returns the
        new address of the location the old address used to point to.
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
        Report contents of block
        '''
        if not self.active :
            self.setActive(True)
        blkstr = "Block - Size: %d, Address: 0x%x, Contents: " % (self.size, self.addr)
        blkstr += repr(self.data.raw)
        return blkstr