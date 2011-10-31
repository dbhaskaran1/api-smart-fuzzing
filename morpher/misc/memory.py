'''
Created on Oct 26, 2011

@author: Rob
'''
import struct
import typeconvert

class Memory(object):
    '''
    classdocs
    '''
    
    def __init__(self, ordinal, blklist):
        '''
        Saves the ordinal of the function that this is a snapshot 
        of, then takes a list of Blocks and adds them to the internal
        memory map. It is assumed that these blocks contain
        non-overlapping ranges of memory and that they will
        not be mutated by an outside source
        '''
        # Dictionary of address -> char[] 
        self.mem = {}
        # Set of object tags in our memory
        self.tags = set()
        # Ordinal of the function we recorded
        self.ordinal = ordinal
        # Address of arguments we recorded
        self.arg_addr = None
        # Format of arguments
        self.arg_fmt = None
        
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
            
    def setArgs(self, addr, fmt):
        '''
        Saves the location and format of the arguments for the
        saved function call
        '''
        self.arg_addr = addr
        self.arg_fmt = fmt
        
    def getArgTypes(self):
        '''
        Turns the fmt type of the snaspshot into a list of ctypes
        '''
        return [typeconvert.fmt2ctype[c] for c in self.arg_fmt ]

    def getArgs(self):
        '''
        Used to return the a list of args for the saved function call
        '''
        types = self.getArgTypes()
        values = self.read(self.arg_addr, fmt=self.arg_fmt)
        return [t.from_param(v) for (t,v) in zip(types, values)]
        
    def addTag(self, tag):
        '''
        Given a tag for an object in this Memory,
        registers the tag
        '''
        size = struct.calcsize(tag.fmt)
        blk = self._findBlock(tag.addr, size)
        if blk == None :
            raise Exception("Address %x size %d not a valid address range" % (tag.addr, size))
        self.tags.add(tag)
        
    def removeTag(self, tag):
        '''
        Removes a tag previously given to addTag
        '''
        self.tags.remove(tag)
    
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
        for tag in self.tags :
            if tag.fmt == "P" :
                blk = self._findBlock(tag.addr, struct.calcsize("P"))
                p = blk.read(tag.addr, fmt="P")[0]
                # Don't try to translate Null
                if p == 0 :
                    continue
                
                tgtblk = self._findBlock(p, 1)
                p = tgtblk.translate(p)
                blk.write(tag.addr, (p,), fmt="P")
            
    def toString(self):
        '''
        Report contents of memory
        '''
        memstr = "\nContents of Memory:\n"
        if self.arg_addr == None :
            memstr += "Ordinal: %d, Arguments and  not specified\n" % self.ordinal
        else :
            memstr += "Ordinal: %d, Argument format: \"%s\", Arguments address: 0x%x\n" \
                        % (self.ordinal, self.arg_fmt, self.arg_addr)
            memstr += "Arguments: " + str(self.getArgs()) + "\n"
        memstr += "Tags: "
        for t in self.tags : 
            memstr += "0x%x - %s   " % (t.addr, t.fmt)
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
        