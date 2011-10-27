'''
Created on Oct 26, 2011

@author: Rob
'''

import multiprocessing
import ctypes
import pickle
import os
from morpher.misc import config

class Harness(multiprocessing.Process):
    '''
    classdocs
    '''
    
    def __init__(self):
        '''
        Constructor
        '''
        multiprocessing.Process.__init__(self)
        cfg = config.Config()
        # cfg.setupLogging()
        # cfg.logConfig()
        self.cfg = cfg
        # self.log = cfg.getLogger(__name__)
        
    def run(self):
        #Load stuff
        print "Harness running"
        
        dlltype = self.cfg.get('fuzzer', 'dlltype')
        path = self.cfg.get('fuzzer', 'target')
        fuzzfile = os.path.join(self.cfg.get('directories', 'datadir'), "fuzzed.pkl")
        
        print path + "  " + fuzzfile
        
        if dlltype == "cdecl" :
            dll = ctypes.cdll
        else :
            dll = ctypes.windll
        target = dll.LoadLibrary(path)
        
        f = open(fuzzfile, "rb")
        m = pickle.load(f)
        f.close()
        
       # for m in call_list :
        print "Ordinal %d ESP %x fmt %s" %(m.ordinal, m.esp, m.arg_fmt)
        print m.mem
        args = m.getArgs()
        print args
        ordinal = m.ordinal
        print target[ordinal](*args)
            
        print "done"
        
       
        