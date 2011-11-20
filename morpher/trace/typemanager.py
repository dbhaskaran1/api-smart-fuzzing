'''
Contains the L{TypeManager} class for storing and reconstructing types

@author: Rob Waaser
@contact: robwaaser@gmail.com
@organization: Carnegie Mellon University
@since: November 13, 2011
'''
import ctypes

class TypeManager(object):
    '''
    Stores type information and can be serialized and reconstructed
    
    Maintains a map of format strings to classes representing the 
    equivalent type. Format strings match the same types used in the
    L{struct} module and can also specify a numeric ID of a user-defined
    type. The information for user-defined types is constructed from
    a supplied dictionary mapping user type ids to a tuple, where the tuple
    contains the type ("struct" or "union") and a list of format strings
    representing each field of that type. This information is used to 
    construct a matching L{ctypes} Structure or Union class on-the-fly
    and add it to the map.
    
    This class is also used to retrieve size and alignment information
    for any type represented by a format string, by using the associated
    L{ctypes} methods on their representative classes. These operations
    are memoized to improve performance, but any information that cannot
    be serialized by the L{pickle} module is discarded upon serialization,
    and the information is reconstructed again after deserialization.
    
    @ivar table: The dictionary mapping format strings to L{ctypes} classes
    @ivar infotable: The memoization table for the L{getInfo} method
    @ivar usertypes: The dictionary storing information about user-defined
                     types such as C Structs and Unions 
    '''

    def __init__(self, usertypes={}):
        '''
        Fills the table mapping format strings to L{ctypes} classes with the
        mappings for the basic types, and stores the information for 
        constructing user-defined types if supplied.
        
        @param usertypes: Optional dictionary mapping format strings to pairs
                          of type strings and lists of fields' formats
        @type usertypes: dictionary of string : (string, string list) pairs
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
        self.infotable = {}
        self.usertypes = usertypes
                
    def __getstate__(self):
        '''
        L{pickle} calls this method when dumping. Prevents the type table
        from being serialized (saves space and time reading in the file)
        
        @return: The __dict__ attibute of this object
        @rtype: dictionary
        '''
        self.table = None
        return self.__dict__
    
    def __setstate__(self, newdict):
        '''
        Pickle calls this method when unpickling. Restores
        the table to the basic state, just like L{__init__}
        
        @param newdict: The state object unserialized by pickle (__dict__)
        @type newdict: dictionary
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
        Given a format string such as "PPi" or "12", etc, returns
        a L{ctypes} class object corresponding to its type,
        creating the class on the fly with the stored usertypes
        data if necessary. The function is memoized for improved
        performance but the memoization table is deleted when
        the object is serialized.
        
        Format strings can be of the types defined by the L{struct}
        module, in which case only the first character is used, or
        the text can represent a number, in which case the usertype
        with the matching id is used. 
        
        @param mytype: The format string to translate to a class
        @type mytype: string
        
        @return: The L{ctypes} class corresponding to the type represented 
                 by the given format string
        @rtype: L{ctypes} class
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
        Performs the reverse of the L{getClass} function.
        
        @param objclass: The {ctypes} class to translate to a format string
        @type objclass: L{ctypes} class
        
        @return: The format string matching the supplied class as described
                 in the L{getClass} function
        @rtype: string
        '''  
        for (key, value) in self.table.items() :
            if value == objclass :
                return key
            
    def getInfo(self, fmt):
        '''
        Takes a format string and returns a (size, alignment) tuple describing
        the size and alignment of the corresponding C type
        
        @param fmt: The format string to translate to a class
        @type fmt: string
        
        @return: A tuple containing the (size, alignment) of the C type
        @rtype: (integer, integer) tuple
        '''  
        if self.infotable.has_key(fmt) :
            return self.infotable[fmt]
        else :
            objclass = self.getClass(fmt)
            size = ctypes.sizeof(objclass)
            align = ctypes.alignment(objclass)
            self.infotable[fmt] = (size, align)
            return (size, align)
    
    def align(self, address, alignment):
        '''
        Utility function to align an address by adding padding
        
        @param address: The address to align
        @type address: integer
        
        @param alignment: The alignment requirement
        @type alignment: integer
        
        @return: The original address plus enough padding that
                 it fits the alignment requirement
        @rtype: integer
        '''
        leftover = (address % alignment)
        padding = (alignment - leftover) % alignment
        return address + padding