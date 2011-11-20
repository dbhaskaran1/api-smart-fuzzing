'''
Contains the L{Trace} class definition for storing a list of L{Snapshot}s

@author: Rob Waaser
@contact: robwaaser@gmail.com
@organization: Carnegie Mellon University
@since: November 13, 2011
'''
from morpher.trace import typemanager

class Trace(object):
    '''
    Pairs a L{TypeManager} object with a list of L{Snapshot} objects.
    
    The L{Snapshot} objects can be replayed in order using the shared
    L{TypeManager} object, which allows this L{Trace} to replay an 
    entire series of function calls exactly as they were first observed.
    
    @note: L{Trace} is built entirely from serializable objects, allowing
           a L{Trace} object to be saved using the L{pickle} module and 
           restored without any noticeable problems  
    '''

    def __init__(self, snapshots, usertypes={}):
        '''
        Uses the supplied usertypes information to create a L{TypeManager}
        object and stores it along with the ordered list of L{Snapshot} objects.
        
        @param snapshots: A list of L{Snapshot} objects in the order they 
                          were captured
        @type snapshots: L{Snapshot} object list
        
        @param usertypes: Optional dictionary mapping format strings to pairs
                          of type strings and lists of fields' formats
        @type usertypes: dictionary of string : (string, string list) pairs
        '''
        self.snapshots = snapshots
        
        self.type_manager = typemanager.TypeManager(usertypes)
        
    def replay(self):
        '''
        Acts as a Python generator function that returns 
        enough information to recreate each function call
        in the trace in order.
        
        Returns a series of pairs, consisting of the function
        ordinal to be replayed and a list of arguments for
        that function.
        
        @return: function ordinals paired with argument lists
        @rtype: (ordinal, L{ctypes} object list)
        '''
        for s in self.snapshots:
            yield (s.ordinal, s.replay(self.type_manager))
            
    def toString(self):
        '''
        Creates a pretty-printed string containing the contents of this
        L{Trace} in a format suitable for display.
        
        @return: A string representing this object's contents
        @rtype: string
        '''
        tracestr = "Trace contents:\n"
        for s in self.snapshots :
            tracestr += "\n" + s.toString() 
        return tracestr