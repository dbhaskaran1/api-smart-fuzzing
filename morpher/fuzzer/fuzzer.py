'''
Contains the L{Fuzzer} class for controlling Morpher fuzzing phase

@author: Rob Waaser
@contact: robwaaser@gmail.com
@organization: Carnegie Mellon University
@since: October 28, 2011     
'''
import os
import pickle
import monitor
import generator
import logging
from morpher.misc import section_reporter

class Fuzzer(object):
    '''
    Top-level class in charge of reading in stored L{Trace}s, fuzzing their
    contents, replaying them back and recording the results.
    
    Most of this class's functionality is reading in L{Trace} files from
    the appropriate directory, then iterating through each L{Tag} for each
    L{Trace}. An internal L{Generator} object is used to get a list of
    fuzzed value for each L{Tag}, and each fuzzed value is used to
    overwrite the original value in turn. Each changed version of the
    L{Trace} is given to a L{Monitor} object for playback, and after all
    versions have been replayed the original value is restored and the
    entire process is repeated for the next tag.
    
    @todo: Possibly expand fuzzing to multiple tags at once
    @todo: Possibly generate L{Trace} for functions we didn't 
           actually collect any data for.
    @todo: Possibly look at fuzzing global variables
    @todo: Possibly fuzz ORDER of function calls, not just data
    @todo: Special fuzzing for arrays and buffers?
    
    @ivar cfg: The L{Config} configuration object for this L{Fuzzer}
    @ivar log: The L{logging} object for this L{Fuzzer}
    @ivar tracenum: The number identifying the current L{Trace}
    @ivar generator: The L{Generator} object used for fuzzing L{Trace} values
    @ivar monitor: The L{Monitor} object used for replaying L{Trace}s.
    '''

    def __init__(self, cfg):
        '''
        Store the configuration object, create a L{Generator} object,
        and set the internal trace number to 0.
        
        @param cfg: The configuration object to use
        @type cfg: L{Config} object
        '''
        self.cfg = cfg
        self.log = logging.getLogger(__name__)
        self.tracenum = 0
        self.generator = generator.Generator(self.cfg)
        self.monitor = None
        
    def fuzz(self):
        '''
        Runs the entire fuzzing process.
        
        If fuzzing is disabled according to the configuration object,
        this function prints a message saying so and returns.
        Otherwise the data\traces directory is searched for L{Trace}
        files, and each one is read into memory.
        
        For each L{Snapshot} in each L{Trace}, the list of L{Tag}s is
        extracted. For each L{Tag}, the original value is saved and
        used to create a list of fuzzed values from the L{Generator}.
        For each fuzzed value, the fuzzed value is used to overwrite the
        original value, and the modified L{Trace} is fed to the 
        L{Monitor} for replay. After every fuzzed version has been run,
        the original value is restored and fuzzing moves on to the next
        tag.
        
        @note: For any fuzzed L{Trace}, only one value is changed 
               from the original version.
               
        @note: A L{SectionReporter} object is instantiated and used
               to track the overall progress for the user.
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
        # This stage is repeated later and is not good for performance -
        # it's done mainly for the SectionReporter, which needs an idea
        # of how much work needs to be done.
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
                for snap in trace.snapshots :
                    numtags += len(snap.tags)
                    
        self.log.info("Counted %s total fuzz targets across all traces", numtags)
        sr = section_reporter.SectionReporter(numtags)
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
            for snap in trace.snapshots :
                self.log.info("Fuzzing next memory image in trace")
                for tag in snap.tags :
                    self.log.info("Fuzzing next tag in memory image")
                    # Store original value for this tag
                    (old,) = snap.mem.read(tag.addr, fmt=tag.fmt)
                    fuzzed_values = self.generator.generate(tag.fmt, old)
                    # Fuzz this tag
                    sr.startSection(tagnum, len(fuzzed_values))
                    for v in fuzzed_values :
                        # Write the fuzzed value
                        snap.mem.write(tag.addr, (v,), fmt=tag.fmt)
                        self.log.info("Sending new fuzzed trace to monitor")
                        self.monitor.run(trace)
                        sr.pulse()
                    # Restore tag value
                    self.log.info("Tag fuzzing complete, restoring value")
                    snap.mem.write(tag.addr, (old,), fmt=tag.fmt)
                    sr.endSection()
                    tagnum += 1
                self.log.info("Memory image fuzzing complete")
            self.log.info("Trace fuzzing complete")
        self.log.info("All traces fuzzed. Fuzzer shutting down")
            
            