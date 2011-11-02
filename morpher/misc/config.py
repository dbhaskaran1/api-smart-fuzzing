'''
config module documentation
'''
import ConfigParser
import os

class Config(ConfigParser.ConfigParser):
    '''
    Config class documentation
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
        debug = params.get("debug", False) or \
                self.get('logging', 'level').lower() == "debug"
        if debug :
            self.set('logging', 'level', "debug")
            
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
            self.set('collector', 'list', params["listfile"])
        elif not self.has_option('collector', 'list') :
            # If no list file supplied, raise error
            raise Exception("No collection list specified in config or command line")
        
    def toString(self):
        '''
        '''
        cfgstr = "\n\n\tConfiguration dump: \n"
        for section in self.sections() :
            cfgstr += "\t[%s]\n" %  section
            for (opt, val) in self.items(section) :
                cfgstr += "\t  %s : %s\n" % (opt, val)
        return cfgstr

        
    