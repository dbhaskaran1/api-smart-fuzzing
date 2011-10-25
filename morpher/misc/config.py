'''
Created on Oct 22, 2011

@author: Rob
'''  
import os
import sys
import optparse
import ConfigParser
import logger
import logging
# Map of global settings (ConfigParser object)
cfg = None
        
def create():
    '''
    Parses command line and config.ini to creates and 
    initialize a new configuration object. Does not use
    logging since the logging system setup is dependent
    on information supplied here
    '''
    global cfg
    cfg = None
    
    # Parse the command line options
    desc = '''
    Morpher is a Python-based tool for fuzzing 32-bit DLLs on Windows. 
    View the included README for documentation and example usage. 
    '''
    use = 'morpher.py [options] [dll]'
    
    p = optparse.OptionParser(description=desc, usage=use)
    
    # Option taking an arg
    p.add_option("-c",action="store",dest="configfile")
    p.add_option("--config-file",action="store",dest="configfile")
    # Option taking an arg
    p.add_option("-l", action="store",dest="listfile")
    p.add_option("--list-file", action="store",dest="listfile")
    # Option taking an arg
    p.add_option("-t", action="store",dest="dll")
    p.add_option("--target", action="store",dest="dll")
    # Option that if present sets a boolean
    p.add_option("-d", action="store_true",dest="debug")
    p.add_option("--debug", action="store_true",dest="debug")
    
    # Defaults
    p.set_defaults(debug=False, configfile="config.ini", listfile=None, dll=None)
    # Returns options list and list of unmatched arguments
    opts, args = p.parse_args()
    
    if len(args) > 0 :
        print "Unrecognized options on command line:",
        for arg in args : print(arg)
        print "Usage: " + use
        sys.exit()
    
    # Now get settings from config file
    # defined variables that can be used by config.ini
    defined = {
        'basedir' : os.getcwd(),
    }
    
    cfg = ConfigParser.ConfigParser(defined)
    cfg.read(opts.configfile)
    
    # Add some more information
    
    # Is debug mode on?
    debug = cfg.get('output', 'debug') or opts.debug
    cfg.set('output', 'debug', debug)
    if debug :
        cfg.set('logging', 'loglevel', "debug")
    # The target DLL to be fuzzed
    if opts.dll != None :
        # If DLL given on command line, overrides config file
        cfg.set('fuzzer', 'target', opts.dll)
    elif not cfg.has_option('fuzzer', 'target') :
        # If no DLL supplied, raise error
        print "No target DLL specified in config or command line"
        sys.exit()
    # The command-line list of programs that use the DLL 
    if opts.listfile != None :
        # If list file given on command line, overrides config file
        cfg.set('collector', 'listfile', opts.listfile)
    elif not cfg.has_option('collector', 'listfile') :
        # If no list file supplied, raise error
        print "No collection list specified in config or command line"
        sys.exit()
    # Where to find the model.xml file
    modelfile = os.path.join(cfg.get('directories', 'datadir'), "model.xml")
    cfg.set('output', 'modelfile', modelfile)
    # Where to save our state as an INI file
    statefile = os.path.join(cfg.get('directories', 'datadir'), "state.ini")
    cfg.set('output', 'statefile', statefile)
        
    return cfg
    
def log() :
    '''
    Report contents of cfg
    '''
    global cfg
    level = logger.level()
    if level <= logging.INFO :
        cfgstr = "\n\n\tConfiguration settings: \n"
        for sec in cfg.sections() :
            cfgstr += "\t[%s]\n" % sec
            for (opt, val) in cfg.items(sec) :
                cfgstr += "\t  %s : %s\n" % (opt, val)
        log = logging.getLogger(__name__)
        log.info(cfgstr)

def save():
    '''
    Save our state to a config file (.ini)
    '''
    filename = cfg.get('output', 'statefile')
    f = open(filename)
    cfg.write(f)
    f.close()
    
def load(filename):
    '''
    If we need to restore our state from saved config file
    '''
    global cfg
    cfg = ConfigParser.ConfigParser()
    cfg.read(filename)

def assign(c):
    '''
    Assigns the given ConfigParser object to cfg
    '''
    global cfg
    cfg = c
