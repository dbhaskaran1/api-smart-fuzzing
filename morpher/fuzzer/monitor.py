'''
Contains the L{Monitor} class for launching and monitoring L{Harness} tasks

@author: Rob Waaser
@contact: robwaaser@gmail.com
@organization: Carnegie Mellon University
@since: October 21, 2011
'''

import multiprocessing
import threading
import harness
from morpher.pydbg import pydbg
from morpher.pydbg import defines
from morpher.utils import crash_binning
import os
import pickle
import shutil
import logging

class Monitor(object):
    '''
    Used for running L{Trace} replays using a L{Harness} and monitoring
    the L{Harness} for crashes, etc.
    
    Acts as a controller for L{Harness} objects - each time L{run} is
    called, a new L{Harness} is spawned, a debugger is attached, and the 
    L{Trace} is sent to the L{Harness} for replay. If a problem is noted
    by the debugger, relevant crash information is assembled and dumped to
    a predetermined directory. Right now two types of "problems" are 
    detected - segmentation faults (access protection violation) and
    hangs over a certain time limit.
    
    @ivar cfg: The L{Config} configuration object for this L{Monitor}
    @ivar log: The L{logging} object for this L{Monitor}
    @ivar limit: Number of seconds to wait for L{Harness} completion 
                 before declaring a timeout.
    @ivar tracenum: The number identifying the current batch of L{Trace}s
    @ivar iter: The number of L{Trace}s run so far for this batch
    @ivar hangpath: The path to the "hangers" directory
    @ivar crashpath: The path to the "crashers" directory
    @ivar last_trace: The last L{Trace} object sent to a L{Harness}
    '''

    def __init__(self, cfg):
        '''
        Takes a config object and sets up Monitor. If data/crashers doesn't
        exist, the directory is created, otherwise all directories inside that 
        start with "address-" are erased. If data/hangers doesn't exist, 
        the directory is created, otherwise all file entries that start with 
        "trace-" and end with ".txt" or ".pkl" are erased.
        
        @param cfg: The configuration object
        @type cfg: L{Config} object
        '''
        # The config object we use for information
        self.cfg = cfg
        # Our personal logging object
        self.log = logging.getLogger(__name__)
        # The number of seconds until we declare a timeout
        self.limit = cfg.getint('fuzzer', 'timeout')
        # The trace and iteration number used to name dump files
        self.tracenum = 0
        self.iter = 0
        # Directories for hang and crash dumps, respectively
        datadir = self.cfg.get('directories', 'data')
        self.hangpath = os.path.join(datadir, "hangers")
        self.crashpath = os.path.join(datadir, "crashers")
        # Clear out the hangers directories
        if os.path.isdir(self.hangpath) :
            for filename in os.listdir(self.hangpath) :
                path = os.path.join(self.hangpath, filename)
                if os.path.isfile(path) and filename.startswith('trace-') and \
                    (filename.endswith('.txt') or filename.endswith('.pkl')):
                    os.remove(path)
        else :
            os.mkdir(self.hangpath)
        # Clear out the crasher directory 
        if os.path.isdir(self.crashpath) :
            for dirname in os.listdir(self.crashpath) :
                path = os.path.join(self.crashpath, dirname)
                if os.path.isdir(path) and dirname.startswith('address-'):
                    shutil.rmtree(path)
        else :
            os.mkdir(self.crashpath)
        # Stores the trace we just sent so we can dump it if needed
        self.last_trace = None
        
    def setTraceNum(self, tracenum):
        '''
        Change the trace number used for naming dump files. Automatically sets 
        the iteration number back to 0
        
        @param tracenum: The new number to use to identify this L{Trace} batch
        @type tracenum: integer
        '''
        self.tracenum = tracenum
        self.iter = 0
        
    def run(self, trace):
        '''
        Takes the L{Trace} and runs it in a L{Harness}, monitoring for crashes.
        
        This function spawns a new process using a L{Harness} object connected
        to this process by a pair of pipes. A debugger is attached to the
        L{Harness} process and handlers are attached to monitor for crashes
        and hangs (defined as the harness not completing by a certain time
        limit). The given L{Trace} is then sent over the pipe to the
        L{Harness} for replay, and the L{Harness} is watched for completion.
        If a crash or hang occurs, relevant information is collected and
        dumped to a file for inspection and possible reproduction.
        
        Each L{Trace} is identified as a certain run (the iteration) of a 
        certain batch (the trace number), and this identification is 
        reflected by the file name if a dump occurs. The scheme is based off
        the common fuzzing pattern of taking one "base" trace and fuzzing the
        values in it to create multiple fuzzed versions - so a batch is all
        traces that were generated by fuzzing the same base trace.
        
        @param trace: The trace to run and monitor
        @type trace: L{Trace} object
        '''
        self.log.info("Monitor is running. Creating pipe and harness")
        self.last_trace = trace
        
        # Spawn a new test harness and connect to it
        (inpipe, outpipe) = multiprocessing.Pipe()
        h = harness.Harness(self.cfg, (inpipe, outpipe))
        
        self.log.info("Running the harness")
        h.start()
        
        #inpipe.close()
        self.inpipe = inpipe
        
        # Attach the debugger to the waiting harness
        pid = h.pid
        self.log.info("Attaching to harness, pid %d", pid)
        dbg = pydbg.pydbg()
        dbg.attach(pid)
        dbg.set_callback(defines.EXCEPTION_ACCESS_VIOLATION, self.crash_handler)
        dbg.set_callback(defines.USER_CALLBACK_DEBUG_EVENT, self.time_check)
        
        # Prepare our timeout object
        self.log.info("Setting timeout to %d seconds", self.limit)
        self.timed_out = False
        t = threading.Timer(self.limit, self.timeout)
        
        if self.log.isEnabledFor(logging.DEBUG) :
            tracestr = trace.toString()
            self.log.debug("Trace %d run %d contents:\n\n%s\n", \
                           self.tracenum, self.iter, tracestr)
        
        # Send the trace
        self.log.info("Sending trace %d run %d, releasing harness", \
                      self.tracenum, self.iter)
        try :
            outpipe.send(trace)
        except :
            msg = "Error sending trace over pipe to harness"
            self.log.exception(msg)
            raise Exception(msg)
        
        # Release the test harness
        t.start()
        dbg.run()
        t.cancel()
        
        outpipe.close()
        self.inpipe.close()
        
        self.iter += 1
        self.log.info("Monitor exiting")
        
    def timeout(self):
        '''
        Sets the timed_out flag. This should be called with a timer 
        after (self.limit) seconds
        '''
        self.timed_out = True
        
    def time_check(self, dbg):
        '''
        Checks for timeouts, in which case it logs the L{Trace} as a "hanger" 
        and terminates the process. 
        
        This function should be set up as the handler for the debugger's
        event loop (which is called at least every 100ms). This function
        checks if a timeout has occurred and if so, drops
        any L{Snapshot}s from the offending L{Trace} that weren't called
        before the timeout occurred, and dumps the information to the 
        "hangers" directory.
        
        Two files are created: a text (.txt) file with the human-readable
        contents of the L{Snapshot}s that lead to the hang, and a pickle 
        (.pkl) file with the same name that contains a pickled version of 
        the hanging L{Trace}, which can be replayed in order to reproduce 
        the hang.
        
        @param dbg: The debug object this was called from
        @type dbg: L{pydbg} object
        '''
        if self.timed_out :
            # Reduce trace to only calls that were made before the hang
            snaps = []
            for s in self.last_trace.snapshots :
                if self.inpipe.poll() and self.inpipe.recv() == True :
                    snaps.append(s)
                else :
                    break

            # Dump  trace string to file
            filename = "trace-%d-run-%d.txt" % (self.tracenum, self.iter)
            dumpfile = os.path.join(self.hangpath, filename)
            f = open(dumpfile, "w")
            for s in snaps :
                f.write(s.toString() + "\n")
            f.close()
            # Dump the trace
            filename = "trace-%d-run-%d.pkl" % (self.tracenum, self.iter)
            dumpfile = os.path.join(self.hangpath, filename)
            f = open(dumpfile, "wb")
            pickle.dump(self.last_trace, f)
            f.close()
            # Terminate the process
            self.log.info("!!! Harness timed out !!!")
            self.log.info("Terminating harness")
            dbg.terminate_process()  
        
    def crash_handler(self, dbg):
        '''
        Handles crash events in the L{Harness}, logs the information
        and terminates.
        
        This function should be set up as the handler for segmentation
        fault events detected by the debugger. This function records the 
        crash information using the L{crash_binning} module, drops
        any L{Snapshot}s from the offending L{Trace} that weren't called
        before the crash occurred, and dumps the information to the 
        "crashers" directory, under a sub-directory matching the address
        of the instruction the crash occurred at.
        
        Two files are created: a text (.txt) file with the human-readable
        crash information and contents of the L{Snapshot}s that lead to
        the crash, and a pickle (.pkl) file with the same name that contains
        a pickled version of the crashing L{Trace}, which can be replayed
        in order to reproduce the crash.
        
        @param dbg: The debug object this was called from
        @type dbg: L{pydbg} object
        
        @return: L{pydbg.defines} DBG_EXCEPTION_NOT_HANDLED
        @rtype: integer
        '''
        # Bin the crash and get the crash dump string
        self.log.info("!!! Registered a crash in the test harness !!!")
        crashbin = crash_binning.crash_binning()
        crashbin.record_crash(dbg)
        crashstr = crashbin.crash_synopsis()
        self.log.debug("\n" + crashstr)
        
        # Create the directory for this bin if not existing
        addr = crashbin.last_crash.exception_address
        dirpath = os.path.join(self.crashpath, "address-" + hex(addr))
        if not os.path.isdir(dirpath):
            os.mkdir(dirpath)
            
        # Reduce trace to only calls that were made before the crash
        snaps = []
        for s in self.last_trace.snapshots :
            if self.inpipe.poll() and self.inpipe.recv() == True :
                snaps.append(s)
            else :
                break
        
        # Dump crash synopsis and trace string to file
        dumpfile = os.path.join(dirpath, "trace-%d-run-%d.txt" % (self.tracenum, self.iter))
        f = open(dumpfile, "w")
        f.write(crashstr)
        
        # Write out the trace information
        for s in snaps :
            f.write(s.toString() + "\n")
        f.close()
        
        # Dump the trace in pickle format
        dumpfile = os.path.join(dirpath, "trace-%d-run-%d.pkl" % (self.tracenum, self.iter))
        f = open(dumpfile, "wb")
        pickle.dump(self.last_trace, f)
        f.close()
                
        # Done reporting, terminate the harness
        self.log.info("Terminating the test harness")
        dbg.terminate_process()
        return defines.DBG_EXCEPTION_NOT_HANDLED