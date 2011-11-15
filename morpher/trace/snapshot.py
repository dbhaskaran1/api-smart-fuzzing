'''
Created on Nov 13, 2011

@author: Rob
'''
import memory
import struct
import ctypes
from morpher.trace import typemanager

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
        # Type Manager
        self.type_manager = None

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
        self.type_manager = None
        return arguments
    
    def toString(self):
        '''
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
        '''
        print str(addr) + " " + str(fmt)
        if objclass == None :
            objclass = self.type_manager.getClass(fmt)
        if issubclass(objclass, ctypes.Structure) :
            offset = 0
            myinst = objclass()
            for (fieldname, fieldclass) in objclass._fields_ :
                fieldfmt = self.type_manager.getFormat(fieldclass)
                (size, alignment) = self.type_manager.getInfo(fieldfmt)
                offset = self.type_manager.align(offset, alignment)
                obj = self._loadObject(addr + offset, fieldfmt, fieldclass)
                setattr(myinst, fieldname, obj)
                offset += size
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
