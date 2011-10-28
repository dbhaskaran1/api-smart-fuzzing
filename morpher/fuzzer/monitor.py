'''
Created on Oct 21, 2011

@author: Rob
'''
import multiprocessing
import threading
import harness
from morpher.pydbg import pydbg
from morpher.pydbg import defines
from morpher.utils import crash_binning
import os
import pickle

class Monitor(object):
    '''
    classdocs
    '''

    def __init__(self, cfg, tracenum):
        '''
        Takes a config object and the "tracenum" to be used in the
        name of dump files (its assumed that one Monitor is used for
        one original trace, and that each run(trace) call corresponds
        to a fuzzed version of the original (called an iteration)
        '''
        self.cfg = cfg
        self.log = cfg.getLogger(__name__)
        self.limit = cfg.getint('fuzzer', 'timeout')
        self.tracenum = tracenum
        self.iter = 0
        datadir = self.cfg.get('directories', 'datadir')
        self.hangpath = os.path.join(datadir, "hangers")
        self.crashpath = os.path.join(datadir, "crashers")
        self.crashbin = crash_binning.crash_binning()
        self.last_trace = None
        
    def run(self, trace):
        '''
        Takes this trace and run it in the harness, monitoring for crashes
        '''
        self.log.info("Monitor is running. Creating pipe and harness")
        self.last_trace = trace
        
        # Spawn a new test harness and connect to it
        (inpipe, outpipe) = multiprocessing.Pipe()
        h = harness.Harness(self.cfg, (inpipe, outpipe))
        
        self.log.info("Running the harness")
        h.start()
        
        inpipe.close()
        
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
        
        # Send the trace
        self.log.info("Sending trace, releasing harness")
        outpipe.send(trace)
        
        # Release the test harness
        t.start()
        dbg.run()
        t.cancel()
        
        self.iter += 1
        self.log.info("Monitor exiting")
        
    def timeout(self):
        '''
        Sets the timed_out flag. Should call with a timer after (MAXTIME) seconds
        '''
        self.timed_out = True
        
    def time_check(self, dbg):
        '''
        Checks for timeouts, in which case it logs the hang and terminates the process.
        Set as handler for debugger's event loop (called at least every 100ms)
        '''
        if self.timed_out :
            print "Program hung and timed out."
            # Dump  trace string to file
            dumpfile = os.path.join(self.hangpath, "trace-%d-run-%d.txt" % (self.tracenum, self.iter))
            f = open(dumpfile, "w")
            for m in self.last_trace :
                m.setActive()
                f.write(m.toString())
            f.close()
            # Dump the trace
            dumpfile = os.path.join(self.hangpath, "trace-%d-run-%d.pkl" % (self.tracenum, self.iter))
            f = open(dumpfile, "wb")
            pickle.dump(self.last_trace, f)
            f.close()
            # Terminate the process
            self.log.info("Harness timed out before running to completion. Terminating.")
            dbg.terminate_process()  
        
    def crash_handler(self, dbg):
        '''
        If we've crashed, record the information and terminate
        '''
        print "Program CRASHED!!!!!!!"
        
        # Bin the crash and get the crash dump string
        self.log.info("Registered a crash in the test harness")
        self.crashbin.record_crash(dbg)
        crashstr = self.crashbin.crash_synopsis()
        self.log.debug("CRASH SYNOPSIS: %s", crashstr)
        
        # Create the directory for this bin if not existing
        addr = self.crashbin.last_crash.exception_address
        dirpath = os.path.join(self.crashpath, "address-" + hex(addr))
        if not os.path.isdir(dirpath):
            os.mkdir(dirpath)
            
        # Dump crash synopsis and trace string to file
        dumpfile = os.path.join(dirpath, "trace-%d-run-%d.txt" % (self.tracenum, self.iter))
        f = open(dumpfile, "w")
        f.write(crashstr)
        for m in self.last_trace :
            m.setActive()
            f.write(m.toString())
        f.close()
        
        # Dump the trace
        dumpfile = os.path.join(dirpath, "trace-%d-run-%d.pkl" % (self.tracenum, self.iter))
        f = open(dumpfile, "wb")
        pickle.dump(self.last_trace, f)
        f.close()
                
        # Done reporting, terminate the harness
        self.log.info("Terminating the test harness")
        dbg.terminate_process()
        return defines.DBG_EXCEPTION_NOT_HANDLED