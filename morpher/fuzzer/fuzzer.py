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
from morpher.misc import parallel_reporter

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
    @ivar pr: The L{ParallelReporter} object used to indicate progress
    @ivar tracenum: The number identifying the current L{Trace}
    @ivar generator: The L{Generator} object used for fuzzing L{Trace} values
    @ivar monitor: The L{Monitor} object used for replaying L{Trace}s.
    @ivar fuzz_pointers: Boolean indicating if pointers should be fuzzed
    @ivar snapshot_mode: String indicating if snapshots should have their tags fuzzed
                         one by one ("sequential") or all at once ("simultaneous")
    @ivar trace_mode: String indicating if traces should have their snapshots fuzzed
                      one by one ("sequential") or all at once ("simultaneous")
    '''

    def __init__(self, cfg):
        '''
        Store the configuration object, create a L{Generator} object,
        and set the internal trace number to 0.
        
        @param cfg: The configuration object to use
        @type cfg: L{Config} object
        '''
        # The config object used for setup info
        self.cfg = cfg
        # The logging object
        self.log = logging.getLogger(__name__)
        # The progress bar object
        self.pr = None
        # The current trace number
        self.tracenum = 0
        # The generator object for creating fuzzed values
        self.generator = generator.Generator(self.cfg)
        # The Monitor object for testing fuzzed traces
        self.monitor = None
        # Boolean indicating if pointers are fair game
        self.fuzz_pointers = True
        # String indicating if snapshots should have their tags fuzzed
        # one by one ("sequential") or all at once ("simultaneous")
        self.snapshot_mode = None
        # String indicating if traces should have their snapshots fuzzed
        # one by one ("sequential") or all at once ("simultaneous")
        self.trace_mode = None
        
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
        tag.The above process describes "sequential" mode for traces and
        snapshots; "simultaneous" mode performs the above steps for all
        tags in a snapshot and/or all snapshots in a trace at the same time.
        
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
        
        self.fuzz_pointers = self.cfg.getboolean('fuzzer', 'fuzz_pointers')
        self.snapshot_mode = self.cfg.get('fuzzer', 'snapshot_mode')
        self.trace_mode = self.cfg.get('fuzzer', 'trace_mode')
        
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
        self.pr = parallel_reporter.ParallelReporter(numtags)
        self.pr.start("  Fuzzer is running...")
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
            for _ in self.fuzzTrace(trace) :
                self.log.info("Sending next trace")
                self.monitor.run(trace)
           
            self.log.info("Trace fuzzing complete")
        self.pr.done()
        self.log.info("All traces fuzzed. Fuzzer shutting down")
            
    def fuzzTrace(self, trace):
        '''
        Takes a L{Trace} to fuzz and returns an iterator object. Each iteration
        modifies the original trace in some way and then returns a reference
        to that trace. The L{Trace} is not restored to its original state after
        the fuzzing is completed.
        
        If trace mode is set to "sequential", each snapshot is fuzzed one at a
        time in the trace, that is, an iterator is obtained using L{fuzzSnapshot}
        for the first snapshot, and the L{Trace} is updated for each fuzzed value
        given by the iterator until the iterator is exhausted. Then the process
        moves to the next L{Snapshot} and so on. In "simultaneous" mode is set,
        the iterators are exercised for all the L{Snapshot}s in the L{Trace}
        simultaneously, until the last iterator is exhausted.
        
        @param trace: The original L{Trace} object to fuzz
        @type trace: L{Trace} object
        
        @return: iterator generating fuzzed L{Trace} objects
        @rtype: Iterator object
        '''
        if self.trace_mode.lower() == "sequential" :
            # Fuzz snapshots one at a time
            self.log.info("Fuzzing snapshots sequentially")
            for snap in trace.snapshots :
                self.log.debug("Fuzzing next snapshot...")
                for _ in self.fuzzSnap(snap) :
                    yield trace
        else :
            # Fuzz all the snapshots at once
            self.log.info("Fuzzing snapshots simultaneously")
            remaining = []
            # Get the iterators
            for snap in trace.snapshots :
                remaining.append(self.fuzzSnap(snap))
            # Run through all iterators until completed
            while len(remaining) > 0 :
                # Fuzz every snapshot
                self.log.debug("Starting next round of fuzzing")
                current = list(remaining)
                for fuzzer in current :
                    try :
                        fuzzer.next()
                    except StopIteration :
                        remaining.remove(fuzzer)
                # Return trace - check that at least one iterator
                # yielded a new value (otherwise all would be removed)
                if len(remaining) > 0 :
                    yield trace
                else :
                    self.log.debug("Snapshot has been totally fuzzed")
                
    
    def fuzzSnap(self, snap):
        '''
        Takes a L{Snapshot} to fuzz and returns an iterator object. Each iteration
        modifies the original snapshot in some way and then returns a reference
        to that snapshot. Once the iterator is exhausted the L{Snapshot} is 
        returned to its original state.
        
        If snapshot mode is set to "sequential", only one tag is fuzzed at a time
        - all the tags but one will retain their original value. If the mode is
        "simultaneous" the fuzzing mode is applied to all the tags at once, i.e. a
        fuzzed value is generated for each tag and the snapshot is returned, and the
        process repeats until all the tags have run out of fuzzed value. If a tag 
        finishes fuzzing before the remaining tags have finished, it retains the
        last fuzzed value it was given until the remaining tags are completed.
        
        @param snap: The original L{Snapshot} object to fuzz
        @type snap: L{Snapshot} object
        
        @return: iterator generating fuzzed L{Snapshots} objects
        @rtype: Iterator object
        '''
        if self.snapshot_mode.lower() == "sequential"  :
            # Fuzz one tag at a time
            self.log.info("Fuzzing tags one at a time")
            for tag in snap.tags :
                # Check if this a pointer and if we're fuzzing them
                if not self.fuzz_pointers and tag.fmt == "P" :
                    self.log.debug("Skipping pointer tag for fuzzing")
                    mychunk = self.pr.getChunk(1)
                    self.pr.endChunk(mychunk)
                else :
                    self.log.debug("Fuzzing next tag in memory image")
                    # Store original value for this tag
                    (old,) = snap.mem.read(tag.addr, fmt=tag.fmt)
                    fuzzed_values = self.generator.generate(tag.fmt, old)
                    # Fuzz this tag
                    mychunk = self.pr.getChunk(len(fuzzed_values))
                    for v in fuzzed_values :
                        # Write the fuzzed value
                        snap.mem.write(tag.addr, (v,), fmt=tag.fmt)
                        yield snap
                        self.pr.pulseChunk(mychunk)
                    # Restore tag value
                    self.log.debug("Tag fuzzing complete, restoring value")
                    snap.mem.write(tag.addr, (old,), fmt=tag.fmt)
                    self.pr.endChunk(mychunk)
        else :
            # Fuzz all the tags at once
            self.log.info("Fuzzing all tags simultaneously")
            remaining = {}
            orig = {}
            chunks = {}
            for tag in snap.tags :
                # Check if this a pointer and if we're fuzzing them
                if not self.fuzz_pointers and tag.fmt == "P" :
                    self.log.debug("Skipping pointer tag for fuzzing")
                    mychunk = self.pr.getChunk(1)
                    self.pr.endChunk(mychunk)
                else :
                    self.log.debug("Getting fuzzed values for tag")
                    # Get fuzzed values for this tag
                    (old,) = snap.mem.read(tag.addr, fmt=tag.fmt)
                    # Store the old value so it can be restored later
                    fuzzed_values = self.generator.generate(tag.fmt, old)
                    orig[tag] = old
                    remaining[tag] = fuzzed_values
                    chunks[tag] = self.pr.getChunk(len(fuzzed_values))
                    

            # Iterate through every fuzzed value of every tag
            while len(remaining) > 0 :
                # Get a fuzzed value for each tag
                self.log.debug("Performing next round of tag fuzzing")
                current = list(remaining.items())
                for (tag, values) in current :
                    # Get next fuzzed value
                    v = values.pop()
                    self.pr.pulseChunk(chunks[tag])
                    # If that was the last value, remove the tag from list
                    if len(values) == 0 :
                        remaining.pop(tag)
                        self.pr.endChunk(chunks[tag])
                    else :
                        remaining[tag] = values
                    # Write the fuzzed value
                    snap.mem.write(tag.addr, (v,), fmt=tag.fmt)
                # Return the fuzzed snapshot
                yield snap

            # Done fuzzing, restore the snapshot
            self.log.debug("All tags fuzzed, restoring snapshot")
            for (tag, value) in orig.items() :
                snap.mem.write(tag.addr, (value,), fmt=tag.fmt)