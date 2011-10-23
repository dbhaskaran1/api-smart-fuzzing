'''
Created on Oct 22, 2011

@author: Rob
'''  
import os
import sys
import optparse
import ConfigParser
 
# Map of global settings
cfg = None

def assign(c):
    '''
    Assigns the given config map to cfg
    '''
    global cfg
    cfg = c
        
def create():
    '''
    Parses command line and config.ini to creates and 
    initialize a new configuration object
    '''
    global cfg
    cfg = None
    
    # Set up the new config object
    desc = '''
    Welcome to API Fuzzer (we need a new name). You need some help, so here it is:
    '''
    use = 'run.py [options] dll1 dll2 ..'
    p = optparse.OptionParser(description=desc, usage=use)
    
    # Option taking an arg
    p.add_option("-c",action="store",dest="configfile")
    p.add_option("--config-file",action="store",dest="configfile")
    # Option that if present sets a boolean
    p.add_option("-d", action="store_true",dest="debug")
    p.add_option("--debug", action="store_true",dest="debug")
    # Defaults
    p.set_defaults(debug=False, configfile="config.ini")
    # Returns options list and list of unmatched arguments
    opts, args = p.parse_args()
    # Retrieve options
    configfile = opts.configfile
    debugmode = opts.debug
    
    if len(args) <= 0 :
        print use
        sys.exit()
    
     = args[0]
    
    #now we get setting from config file
    defaults = {
        'datadir' : "data",
        'crashdir' : "crashers"
    }
    
    cfgreader = ConfigParser.ConfigParser(defaults)
    cfgreader.read(configfile)
    
    datadir = cfgreader.get('input', 'datadir')
    crashdir = cfgreader.get('output', 'crashdir')
    debugmode = cfgreader.get('output', 'debug') or debugmode
    
    cfg 
    cfg[]
    
    if debugmode:
        print "Debug mode ON"
        print "Data directory: %s" % datadir
        print "Crash file directory: %s" % crashdir
        print "DLL: %s" % dll
        print "Path: %s" % (os.getcwd() + '\\' + dll)
        
    return cfg
    
