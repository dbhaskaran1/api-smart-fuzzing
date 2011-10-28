'''
Created on Oct 28, 2011

@author: Rob
'''
import os
import pickle
import monitor

class Fuzzer(object):
    '''
    classdocs
    '''


    def __init__(self, cfg):
        '''
        Constructor
        '''
        self.cfg = cfg
        self.log = cfg.getLogger(__name__)
        self.monitor = monitor.Monitor(self.cfg)
        self.tracenum = 0
    
    def fuzz(self):
        '''
        '''
        # Get the stored traces
        datadir = self.cfg.get('directories', 'datadir')
        tracedir = os.path.join(datadir, "traces")
        self.log.info("Checking trace directory for files: %s", tracedir)
        flist = os.listdir(tracedir)
        for tracefile in flist :
            # Check that this is a trace file
            path = os.path.join(tracedir, tracefile)
            if os.path.isfile(path) and path.endswith(".pkl"):
                # Unpickle the trace
                self.log.info("Loading new trace: %s", tracefile)
                path = os.path.join(tracedir, tracefile)
                f = open(path)
                trace = pickle.load(f)
                f.close()
                # Increment the tracenum
                self.log.info("Trace number set to %d", self.tracenum)
                self.monitor.setTraceNum(self.tracenum)
                self.tracenum += 1
                # FUZZ LOOP STARTS HERE
                self.log.info("Sending new fuzzed trace to monitor")
                self.monitor.run(trace)
                # FUZZ LOOP ENDS HERE
        self.log.info("All traces fuzzed. Fuzzer shutting down")
            
            