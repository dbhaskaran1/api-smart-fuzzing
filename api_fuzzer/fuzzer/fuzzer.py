'''
Created on Oct 21, 2011

@author: Rob
'''
import multiprocessing
import ctypes

class fuzzer(multiprocessing.Process):
    '''
    classdocs
    '''

    def __init__(self, dll):
        '''
        Constructor
        '''
        multiprocessing.Process.__init__(self)
        self.dll = dll
        
    def run(self):
        #Load stuff
        print "Fuzzer starting, file: %s" % self.dll
        target = ctypes.CDLL(self.dll)
        print "Result of add call: %d" % target.add_num(2, 6)