'''
Created on Oct 25, 2011

@author: Rob
'''
from morpher import morpher
import optparse
import sys
import traceback

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

        
    # Returns options list and list of unmatched arguments
    opts, args = p.parse_args()
        
    if len(args) > 0 :
        print "Unrecognized options on command line:",
        for arg in args : print(arg)
        print usage
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