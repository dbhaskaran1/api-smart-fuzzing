'''
Created on Nov 13, 2011

@author: Rob
'''
from morpher.trace import typemanager
class Trace(object):
    '''
    classdocs
    '''


    def __init__(self, model, snapshots):
        '''
        Constructor
        '''
        self.snapshots = snapshots
        self.type_manager = typemanager.TypeManager(model)
        
    def replay(self):
        '''
        '''
        for s in self.snapshots:
            yield (s.ordinal, s.replay(self.type_manager))
            
    def toString(self):
        '''
        '''
        tracestr = "Trace contents:\n"
        for s in self.snapshots :
            tracestr += "\n" + s.toString() 
        return tracestr