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
import shutil
import logging

class Monitor(object):
    '''
    classdocs
    '''

    def __init__(self, cfg):
        '''
        Takes a config object and sets up Monitor. If data/crashers doesn't
        exist, creates it, otherwise erases all directories inside that 
        start with "address-". If data/hangers doesn't exist, creates it,
        otherwise erases all file entries that start with "trace-" and
        end with ".txt" or ".pkl"
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
        Change the trace number used for dumping files. Sets
        iteration number back to 0
        '''
        self.tracenum = tracenum
        self.iter = 0
        
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
        
        # Send the trace
        self.log.info("Sending trace %d run %d, releasing harness", self.tracenum, self.iter)
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
        Sets the timed_out flag. Should call with a timer after (MAXTIME) seconds
        '''
        self.timed_out = True
        
    def time_check(self, dbg):
        '''
        Checks for timeouts, in which case it logs the hang and terminates the process.
        Set as handler for debugger's event loop (called at least every 100ms)
        '''
        if self.timed_out :
            # Reduce trace to only calls that were made before the hang
            trace = []
            for m in self.last_trace :
                if self.inpipe.poll() and self.inpipe.recv() == True :
                    trace.append(m)
                else :
                    break
            # Dump  trace string to file
            dumpfile = os.path.join(self.hangpath, "trace-%d-run-%d.txt" % (self.tracenum, self.iter))
            f = open(dumpfile, "w")
            for m in trace :
                f.write(m.toString())
            f.close()
            # Dump the trace
            dumpfile = os.path.join(self.hangpath, "trace-%d-run-%d.pkl" % (self.tracenum, self.iter))
            f = open(dumpfile, "wb")
            pickle.dump(trace, f)
            f.close()
            # Terminate the process
            self.log.info("!!! Harness timed out !!!")
            self.log.info("Terminating harness")
            dbg.terminate_process()  
        
    def crash_handler(self, dbg):
        '''
        If we've crashed, record the information and terminate
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
        trace = []
        for m in self.last_trace :
            if self.inpipe.poll() and self.inpipe.recv() == True :
                trace.append(m)
            else :
                break
        
        # Dump crash synopsis and trace string to file
        dumpfile = os.path.join(dirpath, "trace-%d-run-%d.txt" % (self.tracenum, self.iter))
        f = open(dumpfile, "w")
        f.write(crashstr)
        
        # Write out the trace information
        for m in trace :
            f.write(m.toString())
        f.close()
        
        # Dump the trace in pickle format
        dumpfile = os.path.join(dirpath, "trace-%d-run-%d.pkl" % (self.tracenum, self.iter))
        f = open(dumpfile, "wb")
        pickle.dump(trace, f)
        f.close()
                
        # Done reporting, terminate the harness
        self.log.info("Terminating the test harness")
        dbg.terminate_process()
        return defines.DBG_EXCEPTION_NOT_HANDLED