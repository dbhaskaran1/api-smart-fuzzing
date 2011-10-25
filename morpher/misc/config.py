'''
Created on Oct 22, 2011

@author: Rob
'''  
import os
import ConfigParser
import logging.handlers
import sys
import atexit
import null

class Config(ConfigParser.ConfigParser):
    
    log = None
    
    def __init__(self, **params):
        '''
        Parses config.ini and given params to create and 
        initialize a new configuration object. Does not use
        logging since the logging system setup is dependent
        on information supplied here
        '''
        ConfigParser.ConfigParser.__init__(self)
        
        # Get settings from config file
        # defined variables that can be used by config.ini
        
        # Set special default values for INI entries
        self.set("DEFAULT", "basedir", os.getcwd())
        
        # Read the config file
        cfgfile = params.pop("configfile", "config.ini")
        self.read(cfgfile)
        
        # Add some more information
        
        # Is debug mode on?
        debug = self.getboolean('output', 'debug') or \
                params.get("debug", False) or \
                self.get('logging', 'loglevel') == "debug"
        self.set('output', 'debug', debug)
        if debug :
            self.set('logging', 'loglevel', "debug")
            
        # The target DLL to be fuzzed
        if params.has_key("dll") :
            # If DLL given on command line, overrides config file
            self.set('fuzzer', 'target', params["dll"])
        elif not self.has_option('fuzzer', 'target') :
            # If no DLL supplied, raise error
            raise Exception("No target DLL specified in config or command line")
        
        # The command-line list of programs that use the DLL 
        if params.has_key("listfile") :
            # If list file given on command line, overrides config file
            self.set('collector', 'listfile', params["listfile"])
        elif not self.has_option('collector', 'listfile') :
            # If no list file supplied, raise error
            raise Exception("No collection list specified in config or command line")
  
        # Where to find the model.xml file
        modelfile = os.path.join(self.get('directories', 'datadir'), "model.xml")
        self.set('output', 'modelfile', modelfile)
        
        # Where to save our state as an INI file
        statefile = os.path.join(self.get('directories', 'datadir'), "state.ini")
        self.set('output', 'statefile', statefile)
    
    def setupLogging(self):
        '''
        Initializes the logging system and resets existing logs
        '''
        # Are we even using logging?
        if not self.getboolean('logging', 'logging') :
            self.log = null.Null()
            return
        
        # Figure out the logging level
        levelstr = self.get('logging','loglevel').lower().strip()
        if levelstr == "debug" :
            level = logging.DEBUG
        elif levelstr == "info" :
            level = logging.INFO
        elif levelstr == "warning" :
            level = logging.WARNING
        elif levelstr == "error" :
            level = logging.ERROR
        else :
            level = logging.CRITICAL
        
        # setup message format
        fmt = logging.Formatter("%(levelname)-10s %(name)-10s %(asctime)s %(message)s" \
                                + " -- %(module)s.%(funcName)s.%(lineno)d")
        
        # Create a handler to print ERROR or higher messages to stderr
        err_hand = logging.StreamHandler(sys.stderr)
        err_hand.setLevel(logging.ERROR)
        err_hand.setFormatter(fmt)
        
        # Create handler that prints to a file
        logdir = self.get('directories','logdir')
        bufsize = self.get('logging', 'bufsize')
        flush = self.get('logging','flushlevel')
        
        path = os.path.join(logdir, 'main.log')
        os.remove(path)
        main_f_hand = logging.FileHandler(path)
        main_f_hand.setFormatter(fmt)
        main_hand = logging.handlers.MemoryHandler(bufsize, flush, main_f_hand)
        
        # Fuzzer needs to log to a different file since its running concurrently
        path = os.path.join(logdir, 'fuzz.log')
        os.remove(path)
        fuzz_f_hand = logging.FileHandler(path)
        fuzz_f_hand.setFormatter(fmt)
        fuzz_hand = logging.handlers.MemoryHandler(bufsize, flush, fuzz_f_hand)
        
        # Create top-level logger "main"
        main_log = logging.getLogger("morpher")
        main_log.setLevel(level)
        main_log.addHandler(main_hand)
        main_log.addHandler(err_hand)
        
        # Cut off fuzzing process's logger from tree and
        # assign it to a seperate log file
        fuzz_log = logging.getLogger("morpher.fuzzer.fuzzer")
        fuzz_log.propagate = False
        fuzz_log.setLevel(level)
        fuzz_log.addHandler(fuzz_hand)
        fuzz_log.addHandler(err_hand)
        
        # Ensure that logs are flushed on exit
        atexit.register(logging.shutdown)
        
        # Self-report
        self.log = logging.getLogger(__name__)
        self.log.info("Logging system initialized, log level: %s", levelstr)
        
    def logLevel(self) :
        '''
        Returns the effective logging.LEVEL object of the root logger
        '''
        if not self.log :
            return logging.FATAL
        else :
            log = logging.getLogger("morpher")
            return log.getEffectiveLevel()   
        
    def logConfig(self) :
        '''
        Report contents of cfg
        '''
        level = self.logLevel()
        if level <= logging.INFO :
            cfgstr = "\n\n\tConfiguration settings: \n"
            for sec in self.sections() :
                cfgstr += "\t[%s]\n" % sec
                for (opt, val) in self.items(sec) :
                    cfgstr += "\t  %s : %s\n" % (opt, val)
            self.log.info(cfgstr)
            
    def getLogger(self, name):
        '''
        Return a fake Null logger if logging not enabled
        Otherwise give a real logger
        '''
        if not self.getboolean('logging', 'logging'):
            return null.Null()
        else :
            return logging.getLogger(name)
    
    def save(self):
        '''
        Save our state to a config file (.ini)
        '''
        filename = self.get('output', 'statefile')
        self.log.info("Saving state to %s", filename)
        f = open(filename)
        self.write(f)
        f.close()
        
    def load(self, filename):
        '''
        If we need to restore our state from saved config file
        '''
        self.log.info("Reading state from %s", filename)
        self.read(filename)

