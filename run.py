'''
Created on Oct 25, 2011

@author: Rob
'''
from morpher import morpher
from morpher.misc import config
import optparse
import sys
import ctypes
import traceback
import pickle

def playback(filename):
    '''
    Can play back a trace manually, allowing the user to attach a debugger
    and step through the trace
    '''
    cfg = config.Config()
    dlltype = cfg.get('fuzzer', 'dlltype')
    path = cfg.get('fuzzer', 'target')
    
    # Load the target DLL
    if dlltype == "cdecl" :
        dll = ctypes.cdll
    else :
        dll = ctypes.windll
        
    print "Loading " + dlltype + " DLL at " + path
    target = dll.LoadLibrary(path)
    
    print "Replaying trace: " + filename
    f = open(filename, "rb")
    trace = pickle.load(f)
    f.close()
    
    # Run each function capture in order
    for m in trace :
        args = m.getArgs()
        ordinal = m.ordinal
        cmd = "m"
        while not cmd == "" :
            cmd = raw_input("Calling function ordinal %d [Enter to continue, m to show memory]:" % ordinal)
            if cmd == "m" :
                print m.toString()
            
        result = target[ordinal](*args)
        print "Function returned result: %s" % str(result)
        
    print "Trace complete"

if __name__ == '__main__':
    
    # Parse the command line options
    desc = '''
    Morpher is a Python-based tool for fuzzing 32-bit DLLs on Windows. 
    View the included README for documentation and example usage. 
    '''
    usage = 'usage: %prog [options] [dll]'
        
    p = optparse.OptionParser(description=desc, usage=usage)
        
    # Option taking an arg
    p.add_option("-c", "--config-file", action="store",dest="configfile", \
                 help="The INI configuration file to read from")
    # Option taking an arg
    p.add_option("-l", "--list-file", action="store",dest="listfile", \
                 help="The file containing a list of programs to record")
    # Option taking an arg
    p.add_option("-t", "--target", action="store",dest="dll", \
                 help="The name of the DLL we are fuzzing")
    # Option that if present sets a boolean
    p.add_option("-d", "--debug", action="store_true",dest="debug", \
                 help="Flag to enable debug-level output")
    # Option taking an arg
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