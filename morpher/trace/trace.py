'''
Created on Nov 13, 2011

@author: Rob
'''
from morpher.trace import typemanager
class Trace(object):
    '''
    classdocs
    '''


    def __init__(self, model, call_list):
        '''
        Constructor
        '''
        self.call_list = call_list
        self.type_manager = typemanager.TypeManager(model)
        
    def replay(self):
        '''
        '''
        for call in self.call_list:
            yield call.replay(self.type_manager)
        