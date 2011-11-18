'''
Contains the L{Tag} class definition for pairing addresses with types

@author: Rob Waaser
@contact: robwaaser@gmail.com
@organization: Carnegie Mellon University
@since: October 30, 2011
'''

class Tag(object):
    '''
    Pairs an address with a format string representing the type of the
    object located at that address, as an immutable object. The class
    also overrides the L{__hash__} and L{__eq__} methods so that, when
    added to a set, the set will recognize two Tags with equivalent
    information as the same object.
    
    @ivar addr: The address being tagged
    @ivar fmt: The format string associated with the address 
    '''

    def __init__(self, addr, fmt):
        '''
        Initializes this tag with the given address/format pair
        
        @param addr: The address for this tag
        @type addr: integer
        
        @param fmt: The format string representing the associated tag
        @type fmt: string
        '''
        object.__setattr__(self, "addr", addr)
        object.__setattr__(self, "fmt", fmt)
        
    def __eq__(self, other):
        '''
        Compare this object to another L{Tag} object
        
        @param other: A L{Tag} object to compare to
        @type other: L{Tag} object
        
        @return: I{True} if this object matches the given one
        @rtype: Boolean
        '''
        return self.addr == other.addr and self.fmt == other.fmt

    def __hash__(self):
        '''
        Returns a hash constructed from the address and format
        
        @return: A unique hash for this object
        @rtype: integer
        '''
        return hash(self.addr) + 7*hash(self.fmt)
        
    def __setattr__(self, *args):
        '''
        Raise an exception if a change to the object is attempted
        @raise TypeError: Always
        '''
        raise TypeError("Immutable type")
    
    def __delattr__(self, *args):
        '''
        Raise an exception if a change to the object is attempted
        @raise TypeError: Always
        '''
        raise TypeError("Immutable type")