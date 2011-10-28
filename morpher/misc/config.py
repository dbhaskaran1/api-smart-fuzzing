'''
Created on Oct 22, 2011

@author: Rob
'''  
import os
import ConfigParser
import logging
import sys
import atexit
import null

class Config(ConfigParser.ConfigParser):
    '''
    Class documentation
    '''
    
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
        
        # Create the 'temp' section for volatile data
        self.add_section('TEMP')
        
        # Read the config file
        cfgfile = params.pop("configfile", "config.ini")
        self.read(cfgfile)
        
        # Add some more information
        
        # Is debug mode on?
        debug = self.getboolean('output', 'debug') or \
                params.get("debug", False) or \
                self.get('logging', 'loglevel') == "debug"
        self.set('output', 'debug', "on" if debug else "off")
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
    
    def setupLogging(self, root):
        '''
        Initializes the logging system and resets existing logs for given root
        '''
        # Are we even using logging?
        if not self.getboolean('logging', 'log') :
            return
        
        # Figure out the logging level
        level = self.logLevel()
        
        # setup message format
        fmt = logging.Formatter("%(levelname)-10s %(name)-10s %(asctime)s %(message)s" \
                                + " -- %(module)s.%(funcName)s.%(lineno)d")
        
        # Create a handler to print ERROR or higher messages to stderr
        err_hand = logging.StreamHandler(sys.stderr)
        err_hand.setLevel(logging.ERROR)
        err_hand.setFormatter(fmt)
        
        # Create handler that prints to a file
        logdir = self.get('directories','logdir')

        # Clear our log path
        path = os.path.join(logdir, root + ".log")
        if os.path.isfile(path) :
            os.remove(path)
    
        file_hand = logging.FileHandler(path)
        file_hand.setFormatter(fmt)
        
        # Create top-level logger "main"
        main_log = logging.getLogger(root)
        main_log.propagate = False
        main_log.setLevel(level)
        main_log.addHandler(file_hand)
        main_log.addHandler(err_hand)
        
        # Ensure that logs are flushed on exit
        atexit.register(logging.shutdown)
        
        # Self-report
        log = logging.getLogger(root)
        levelstr = self.get('logging','loglevel')
        log.info("Logging system initialized, log level: %s", levelstr)
        
    def logLevel(self) :
        '''
        Returns the effective logging.LEVEL object of the root logger
        '''
        levelstr = self.get('logging','loglevel')
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
        return level
        
            
    def getLogger(self, name):
        '''
        Return a fake Null logger if logging not enabled
        Otherwise give a real logger
        '''
        if not self.getboolean('logging', 'log'):
            return null.Null()
        else :
            return logging.getLogger(name)
        
    def toString(self) :
        '''
        Report contents of cfg
        '''
        cfgstr = "\n\n\tConfiguration settings: \n"
        for sec in self.sections() :
            cfgstr += "\t[%s]\n" % sec
            for (opt, val) in self.items(sec) :
                cfgstr += "\t  %s : %s\n" % (opt, val)
        return cfgstr
    
    '''
    def save(self):
        
        #Save our state to a config file (.ini). Does not store
        #any info in the 'temp' section
        
        # Remove temps from config
        tlist = self.items('TEMP')
        self.remove_section('TEMP')
        # Save the config
        filename = self.get('output', 'statefile')
        self.log.info("Saving state to %s", filename)
        f = open(filename)
        self.write(f)
        f.close()
        # Restore temps
        self.add_section('TEMP')
        for (op, val) in tlist :
            self.set('TEMP', op, val)
        
        
    def load(self, filename):
        
        #If we need to restore our state from saved config file
        
        self.log.info("Reading state from %s", filename)
        self.read(filename)
    '''
