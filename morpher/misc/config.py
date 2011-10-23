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
    initialize a new configuration object
    '''
    global cfg
    cfg = None
    
    # Parse the command line options
    desc = '''
    Morpher is a Python-based tool for fuzzing 32-bit DLLs on Windows. 
    View the included README for documentation and example usage. 
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
    
    if len(args) != 1 :
        if len(args) > 1 :
            print("Multiple target DLLs specified:",)
            for dll in args : print(dll)
        else :
            print("Missing a target DLL")
        print(use)
        sys.exit()
    
    dll = args[0]
    
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
    cfg.set('fuzzer', 'target', dll)
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
        cfgstr += "\n"
        log = logging.getLogger(__name__)
        log.info(cfgstr)

def save():
    '''
    Save our state to a config file (.ini)
    '''
    filename = cfg.get('output', 'statefile')
    f = open(filename)
    cfg.write(f)
    
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
