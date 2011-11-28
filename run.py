'''
Contains a script that serves as a command-line interface to the L{Morpher}
fuzzing tool. 

L{Morpher} is implemented as an object that is mostly controlled
by the contents of a configuration file, but it can have some of the config
file overriden by options specified when the L{Morpher} object is instantiated.
This script parses those options from the command line, passes them to
the L{Morpher} object it instantiates, and sets the entire fuzzing process
running. In addition, this script can start a L{Trace} replay process useful
for analyzing the results of a fuzzing run instead of starting the 
L{Morpher} process.

@author: Rob Waaser
@contact: robwaaser@gmail.com
@organization: Carnegie Mellon University
@since: October 25, 2011
'''

from morpher import morpher
from morpher.misc import config
import optparse
import sys
import os
import ctypes
import traceback
import pickle

def playback(filename):
    '''
    Can play back a trace manually, allowing the user to attach a debugger
    and step through the trace at their own leisure. 
    
    This function was developed to aid a reverse engineer after they have
    run L{Morpher} and wish to investigate the reported crashs and hangs
    in more detail. L{Morpher} stores a copy of the L{Trace} file that
    caused a crash or hang along with the crash report. This function 
    takes the trace file and replays the L{Snapshot}s one at a time,
    reporting the PID so the engineer can attach a debugger of his 
    own and follow along.
    
    @param filename: The path to the L{Trace} file to be replayed
    @type filename: string
    '''
    cfg = config.Config()
    dlltype = cfg.get('fuzzer', 'dll_type')
    path = cfg.get('fuzzer', 'target')
    
    print "Attach your debugger to PID %d" % os.getpid()
    
    # Load the target DLL
    if dlltype == "cdecl" :
        dll = ctypes.cdll
    else :
        dll = ctypes.windll
    
    print "Loading " + dlltype + " DLL at " + path
    target = dll.LoadLibrary(path)
    
    # Load the target trace file
    print "Replaying trace: " + filename
    f = open(filename, "rb")
    trace = pickle.load(f)
    f.close()
    
    # Run each function capture in order
    for s in trace.snapshots :
        name = s.name
        cmd = "s"
        while not cmd == "" :
            print "Calling function %s" % name
            cmd = raw_input("[Enter to continue, s to show snapshot, q to quit]:")
            if cmd == "s" :
                print s.toString()
            elif cmd == "q" :
                print "Quitting..."
                return
                
        args = s.replay(trace.type_manager)
        func = getattr(target, name)
        result = func(*args)
        print "Function returned result: %s" % str(result)
        
    print "Trace complete"

# This is the start of the command-line script
if __name__ == '__main__':
    
    # Parse the command line options
    desc = '''
    Morpher is a Python-based tool for fuzzing 32-bit DLLs on Windows. 
    View the included README for documentation and example usage. 
    '''
    usage = 'usage: %prog [options] [dll]'
        
    p = optparse.OptionParser(description=desc, usage=usage)
        
    # Option specifying the config file
    p.add_option("-c", "--config-file", action="store",dest="configfile", \
                 help="The INI configuration file to read from")
    # Option specifying the list file
    p.add_option("-l", "--list-file", action="store",dest="listfile", \
                 help="The file containing a list of programs to record")
    # Option specifying the target DLL
    p.add_option("-t", "--target", action="store",dest="dll", \
                 help="The name of the DLL we are fuzzing")
    # Option turning on debugging mode
    p.add_option("-d", "--debug", action="store_true",dest="debug", \
                 help="Flag to enable debug-level output")
    # Option to run in playback mode instead of Morpher
    p.add_option("-p", "--playback", action="store",dest="playback", \
                 help="Specify a .pkl trace file to play back")
        
    # Returns options list and list of unmatched arguments
    opts, args = p.parse_args()
        
    if len(args) > 0 :
        print "Unrecognized options on command line:",
        for arg in args : print(arg)
        print usage
        sys.exit()

    # Check for playback routine
    if not opts.playback == None :
        playback(opts.playback)
        sys.exit()

    # Pull out all options that were actually specified        
    params = {}
    
    for (key, value) in opts.__dict__.items() :
        if value != None :
            params[key] = value
    
    # Run Morpher
    try :
        m = morpher.Morpher(**params)
        m.run()
    except:
        traceback.print_exc()
        sys.exit()