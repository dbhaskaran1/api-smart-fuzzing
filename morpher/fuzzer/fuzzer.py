'''
Created on Oct 28, 2011

@author: Rob
'''
import os
import pickle
import monitor
import mutator
import logging

class Fuzzer(object):
    '''
    classdocs
    '''


    def __init__(self, cfg):
        '''
        Constructor
        '''
        self.cfg = cfg
        self.log = logging.getLogger(__name__)
        self.monitor = monitor.Monitor(self.cfg)
        self.mutator = mutator.Mutator(self.cfg)
        self.tracenum = 0
    
    def fuzz(self):
        '''
        '''
        # Get the stored traces
        datadir = self.cfg.get('directories', 'data')
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
                # Main fuzzing loop
                for mem in trace :
                    self.log.info("Fuzzing next memory image in trace")
                    for tag in mem.tags :
                        self.log.info("Fuzzing next tag in memory image")
                        # Store original value for this tag
                        (old,) = mem.read(tag.addr, fmt=tag.fmt)
                        fuzzed_values = self.mutator.mutate(tag.fmt, old)
                        # Fuzz this tag
                        for v in fuzzed_values :
                            # Write the fuzzed value
                            mem.write(tag.addr, (v,), fmt=tag.fmt)
                            self.log.info("Sending new fuzzed trace to monitor")
                            self.monitor.run(trace)
                        # Restore tag value
                        self.log.info("Tag fuzzing complete, restoring value")
                        mem.write(tag.addr, (old,), fmt=tag.fmt)
                    self.log.info("Memory image fuzzing complete")
                self.log.info("Trace fuzzing complete")
        self.log.info("All traces fuzzed. Fuzzer shutting down")
            
            