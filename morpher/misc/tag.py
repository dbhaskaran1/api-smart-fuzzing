'''
Created on Oct 30, 2011

@author: Rob
'''

class Tag(object):
    '''
    classdocs
    '''

    def __init__(self, addr, fmt):
        '''
        Constructor
        '''
        object.__setattr__(self, "addr", addr)
        object.__setattr__(self, "fmt", fmt)
        
    def __eq__(self, other):
        return self.addr == other.addr and self.fmt == other.fmt

    def __hash__(self):
        return hash(self.addr) + 7*hash(self.fmt)
        
    def __setattr__(self, *args):
        raise TypeError("Immutable type")
    
    def __delattr__(self, *args):
        raise TypeError("Immutable type")