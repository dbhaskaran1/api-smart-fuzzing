'''
Created on Nov 13, 2011

@author: Rob
'''
import ctypes

class TypeManager(object):
    '''
    classdocs
    '''

    def __init__(self, model=None):
        '''
        Constructor
        '''
        self.table = {
                    "c": ctypes.c_char,
                    "b": ctypes.c_byte,
                    "B": ctypes.c_ubyte,
                    "h": ctypes.c_short,
                    "H": ctypes.c_ushort,
                    "i": ctypes.c_int,
                    "I": ctypes.c_uint,
                    "l": ctypes.c_long,
                    "L": ctypes.c_ulong,
                    "q": ctypes.c_longlong,
                    "Q": ctypes.c_ulonglong,
                    "f": ctypes.c_float,
                    "d": ctypes.c_double,
                    "P": ctypes.c_void_p
                    }
        self.usertypes = {}
        # Record enough data to reconstruct custom types
        # after being pickled and unpickled
        if not model == None :
            for usernode in model.getElementsByTagName("usertype"):
                myid = usernode.getAttribute("id")
                mytype = usernode.getAttribute("type")
                myparams = []
                for childnode in usernode.getElementsByTagName("param") :
                    myparams.append(childnode.getAttribute("type"))
                self.usertypes[myid] = (mytype, myparams)
                
    def __getstate__(self):
        '''
        Pickle calls this method when dumping. Don't record
        the table (saves space and time reading in file)
        '''
        self.table = None
        return self.__dict__
    
    def __setstate__(self, newdict):
        '''
        Pickle calls this method when unpickling. Restore
        the table to basic state
        '''
        self.__dict__ = newdict
        self.table = {
                    "c": ctypes.c_char,
                    "b": ctypes.c_byte,
                    "B": ctypes.c_ubyte,
                    "h": ctypes.c_short,
                    "H": ctypes.c_ushort,
                    "i": ctypes.c_int,
                    "I": ctypes.c_uint,
                    "l": ctypes.c_long,
                    "L": ctypes.c_ulong,
                    "q": ctypes.c_longlong,
                    "Q": ctypes.c_ulonglong,
                    "f": ctypes.c_float,
                    "d": ctypes.c_double,
                    "P": ctypes.c_void_p
                    }
        
    def getClass(self, mytype):
        '''
        Given a type such as "PPi" or "12", etc, returns
        a ctypes class object corresponding to its type,
        creating the entry on the fly with the stored model
        data if necessary
        '''  
        if self.table.has_key(mytype) :
            # If we've already created this type, return it
            return self.table[mytype]
        if not mytype.isdigit() :
            # Return basic type
            return self.table[mytype[0]]
        # This is a custom type we haven't created yet - get node
        (usertype, userparams) = self.usertypes[mytype]
        # Construct the new class
        class_str = "class %s(ctypes.%s):\n    pass"
        if usertype == "struct" :
            supertype = "Structure"
        else :
            supertype = "Union"
        classname = "Type" + mytype
        exec (class_str % (classname, supertype))
        myclass = eval(classname)
        
        # Populate the class with field types
        fieldlist = []
        for (index, param) in enumerate(userparams) :
            fieldname = "field_" + str(index)
            fieldclass = self.getClass(param)
            fieldlist.append((fieldname, fieldclass))
            
        myclass._fields_ = fieldlist
        # Add the class to our internal dictionary
        self.table[mytype] = myclass
        return myclass
    
    def getFormat(self, objclass):
        '''
        '''
        for (key, value) in self.table.items() :
            if value == objclass :
                return key
            
    def getInfo(self, objclass):
        '''
        '''
        return (ctypes.sizeof(objclass), ctypes.alignment(objclass))
    
    def align(self, address, alignment):
        '''
        Utility function to align an address by adding padding
        '''
        leftover = (address % alignment)
        padding = (alignment - leftover) % alignment
        return address + padding