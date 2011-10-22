'''
Created on Oct 21, 2011

@author: Rob
'''
import optparse
import sys
import ConfigParser 
import api_fuzzer.fuzzer.fuzzer as fuzzer

if __name__ == '__main__':
    
    desc = '''
    Welcome to API Fuzzer (we need a new name).
    You need some help, so here it is:
    '''
    use = 'run.py [options] dll1 dll2 ..'
    p = optparse.OptionParser(description=desc, usage=use)
    
    #option taking an arg
    p.add_option("-c",action="store",dest="configfile")
    p.add_option("--config-file",action="store",dest="configfile")
    #option that if present sets a boolean
    p.add_option("-d", action="store_true",dest="debug")
    p.add_option("--debug", action="store_true",dest="debug")
    #defaults
    p.set_defaults(debug=False, configfile="config.ini")
    #returns options list and list of unmatched arguments
    opts, args = p.parse_args()
    #retrieve options
    configfile = opts.configfile
    debugmode = opts.debug
    
    if len(args) <= 0 :
        print "Need to specify a dll"
        sys.exit()
    
    dll = args[0]
    
    #now we get setting from config file
    defaults = {
        'datadir' : "data",
        'crashdir' : "crashers"
    }
    
    cfg = ConfigParser.ConfigParser(defaults)
    cfg.read(configfile)
    
    datadir = cfg.get('input', 'datadir')
    crashdir = cfg.get('output', 'crashdir')
    debugmode = cfg.get('output', 'debug') or debugmode
    
    if debugmode:
        print "Debug mode ON"
        print "Data directory: %s" % datadir
        print "Crash file directory: %s" % crashdir
        print "DLL: %s" % dll
    
    fuzz = fuzzer.fuzzer(dll)
    fuzz.start()
    pid = fuzz.pid
    
    
    