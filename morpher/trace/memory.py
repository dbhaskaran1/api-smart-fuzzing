'''
Created on Oct 26, 2011

@author: Rob
'''
import struct

class Memory(object):
    '''
    classdocs
    '''
    
    def __init__(self, blklist):
        '''
        Saves the ordinal of the function that this is a snapshot 
        of, then takes a list of Blocks and adds them to the internal
        memory map. It is assumed that these blocks contain
        non-overlapping ranges of memory and that they will
        not be mutated by an outside source
        '''
        # Dictionary of address -> char[] 
        self.mem = {}
        # Set of addresses of pointers
        self.pointers = set()
        
        for b in blklist :
            if not b.active :
                b.setActive(True)
            self.mem[b.addr] = b
            
    def __getstate__(self):
        '''
        Pickle calls this method when dumping. We turn off all the
        blocks so they can be pickled, then give it our __dict__ as
        thats what pickle normally uses. Note that the blocks will 
        automatically re-activate themselves individually when an
        operation is performed on them - otherwise you can use 
        setActive to force them all to reactivate right then
        '''
        for b in self.mem.values() :
            b.setActive(False)
        return self.__dict__
    
    def __setstate__(self, newdict):
        '''
        Pickle calls this method when unpickling. We restore our __dict__,
        then use the opportunity to turn all our blocks back on
        '''
        self.__dict__ = newdict
        for b in self.mem.values() :
            b.setActive(True)
            
    def setActive(self):
        '''
        Utility method to re-enable this object after pickling it
        '''
        for b in self.mem.values() :
            b.setActive(True)
            
    def registerPointer(self, addr):
        '''
        '''
        size = struct.calcsize("P")
        if not self.containsAddress(addr, size):
            raise Exception("Pointer address is not valid")
        self.pointers.add(addr)
        
    def unregisterPointer(self, addr):
        '''
        '''
        self.pointers.discard(addr)
            
    def read(self, addr, size = None, fmt = None):
        '''
        Given an address in this Memory and a size in bytes,
        returns 'size' raw bytes present at that address. If
        an optional format of the type specified in the struct
        module is given, the size parameter is ignored and the fmt
        is used to unpack and return the contents as a tuple of objects
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
        Given an address in this Memory and an array of raw bytes,
        updates the memory at that address in this Memory. If a
        struct-style format is given, data is interpreted as a
        tuple of objects that should be first packed into 
        a byte string before being written to memory
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
        For each pointer in our Memory whose address is registered,
        we update its value to point to the ACTUAL address of the
        same object it originally pointed to
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
        '''
        return self._findBlock(addr, size) != None
    
    def toString(self):
        '''
        Report contents of memory
        '''
        memstr = "\nContents of Memory:\n"
        memstr += "Pointers: "
        for p in self.pointers : 
            memstr += "0x%x  " % (p)
        memstr += "\n"
        for b in self.mem.values():
            memstr += b.toString() + "\n"
        return memstr
        
    def _findBlock(self, addr, size):
        '''
        Given an address and a size, return the appropriate block or None 
        if such a range is not covered by a block
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
        