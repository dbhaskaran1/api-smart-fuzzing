'''
Created on Nov 13, 2011

@author: Rob
'''
import memory
import struct
import ctypes

class Snapshot(object):
    '''
    classdocs
    '''


    def __init__(self, ordinal, blklist):
        '''
        Constructor
        '''
        # Our internal memory snapshot
        self.mem = memory.Memory(blklist)
        # Set of object tags in our memory
        self.tags = set()
        # Ordinal of the function we recorded
        self.ordinal = ordinal
        # Ordered list of argument tags
        self.args = []

    def setArgs(self, args):
        '''
        Saves an ordered list of argument tags for this function call
        '''
        self.args = args
        
    def addTag(self, tag):
        '''
        Given a tag for an object in this Memory,
        registers the tag
        '''
        size = struct.calcsize(tag.fmt)
        if not self.mem.containsAddress(tag.addr, size) : 
            raise Exception("Address %x size %d not a valid address range" % (tag.addr, size))
        self.tags.add(tag)
        if tag.fmt == "P" :
            self.mem.registerPointer(tag.addr)
        
    def removeTag(self, tag):
        '''
        Removes a tag previously given to addTag
        '''
        self.tags.remove(tag)
        if tag.fmt == "P" :
            self.mem.unregisterPointer(tag.addr)
        
    def replay(self, typeman):
        '''
        '''
        self.type_manager = typeman
        self.mem.patch()
        arguments = []
        for tag in self.args :
            arg = self._loadObject(tag.addr, tag.fmt)
            arguments.append(arg)
        return arguments
        
    def _loadObject(self, addr, fmt, objclass=None):
        '''
        '''
        print str(addr) + " " + str(fmt)
        if objclass == None :
            objclass = self.type_manager.getClass(fmt)
        if issubclass(objclass, ctypes.Structure) :
            curaddr = addr
            myinst = objclass()
            for (fieldname, fieldclass) in objclass._fields_ :
                (size, alignment) = self.type_manager.getInfo(fieldclass)
                curaddr = self.type_manager.align(curaddr, alignment)
                if not issubclass(fieldclass, ctypes.Structure) and \
                   not issubclass(fieldclass, ctypes.Union) :
                    fieldfmt = self.type_manager.getFormat(fieldclass)
                else :
                    fieldfmt = None
                obj = self._loadObject(curaddr, fieldfmt, fieldclass)
                setattr(myinst, fieldname, obj)
                curaddr += size
            print fieldname
            print getattr(myinst, fieldname)
            return myinst
        elif issubclass(objclass, ctypes.Union) :
            # Use the biggest field
            myinst = objclass()
            maxsize = 0
            maxfieldname = None
            maxfieldclass = None
            for (fieldname, fieldclass) in objclass._fields_ :
                (size, _) = self.type_manager.getInfo(fieldclass)
                if size > maxsize :
                    maxsize = size
                    maxfieldname = fieldname
                    maxfieldclass = fieldclass
            if not issubclass(maxfieldclass, ctypes.Structure) and \
               not issubclass(maxfieldclass, ctypes.Union) :
                maxfieldfmt = self.type_manager.getFormat(maxfieldclass)
            obj = self._loadObject(addr, maxfieldfmt, maxfieldclass)
            setattr(myinst, maxfieldname, obj)
            return myinst
        else :
            v = self.mem.read(addr, fmt=fmt)[0] 
            return objclass(v)
