'''
Created on Oct 28, 2011

@author: Rob
'''
import os
import pickle
import monitor
import mutator
import logging
from morpher.misc import sectionreporter

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
        self.tracenum = 0
        self.mutator = mutator.Mutator(self.cfg)
        
    def fuzz(self):
        '''
        '''
        # Check if fuzzing is enabled
        if not self.cfg.getboolean('fuzzer', 'enabled') : 
            print "  Fuzzer DISABLED\n"
            self.log.info("Fuzzing is off")
            return
        
        # Set up the monitor here since it cleans directories
        self.monitor = monitor.Monitor(self.cfg)
        
        # Get the stored traces
        datadir = self.cfg.get('directories', 'data')
        tracedir = os.path.join(datadir, "traces")
        self.log.info("Checking trace directory for files: %s", tracedir)
        flist = os.listdir(tracedir)
        # Sort out which files are traces and add up the number of tags
        numtags = 0;
        filelist = []
        for tracefile in flist :
            # Check that this is a trace file
            path = os.path.join(tracedir, tracefile)
            if os.path.isfile(path) and path.endswith(".pkl"):
                # Add to file list
                filelist.append(path)
                f = open(path)
                trace = pickle.load(f)
                f.close()
                for mem in trace :
                    numtags += len(mem.tags)
                    
        self.log.info("Counted %s total fuzz targets across all traces", numtags)
        sr = sectionreporter.SectionReporter(numtags)
        sr.start("  Fuzzer is running...")
        tagnum = 1
        for tracefile in filelist :
            # Unpickle the trace
            self.log.info("Loading new trace: %s", tracefile)
            f = open(tracefile)
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
                    sr.startSection(tagnum, len(fuzzed_values))
                    for v in fuzzed_values :
                        # Write the fuzzed value
                        mem.write(tag.addr, (v,), fmt=tag.fmt)
                        self.log.info("Sending new fuzzed trace to monitor")
                        self.monitor.run(trace)
                        sr.pulse()
                    # Restore tag value
                    self.log.info("Tag fuzzing complete, restoring value")
                    mem.write(tag.addr, (old,), fmt=tag.fmt)
                    sr.endSection()
                    tagnum += 1
                self.log.info("Memory image fuzzing complete")
            self.log.info("Trace fuzzing complete")
        self.log.info("All traces fuzzed. Fuzzer shutting down")
            
            