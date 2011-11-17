'''
Contains the L{Config} class definition

@author: Rob Waaser
@contact: robwaaser@gmail.com
@organization: Carnegie Mellon University
@since: October 22, 2011
'''
import ConfigParser
import os

class Config(ConfigParser.ConfigParser):
    '''
    A wrapper for Python's L{ConfigParser} class which adds
    some project-specific configuration and a toString method.
    
    Inherits from Pythons' standard L{ConfigParser} class, which is used
    to read in files in the well-known INI format and parse them for 
    configuration information. Config overrides the L{__init__} method
    with it's own version, which does some project-specific configuration,
    and also adds a toString method, which returns a pretty-printed string
    useful for logging the state of this Config object.
    
    Config is designed to be used as a central registry of configuration
    information for a project, and after it is initialized with the contents
    of a configuration file, it should be passed to every object in the project
    that needs to access configuration information. Each object can then use
    their individual reference to the global Config object to read and write
    key-value pairs as necessary, which can be seen by all other objects as well.
    
    @note: Config is naturally pickleable as long as no key-value pairs are
           added that contain pickleable objects - meaning it can be used to
           store a programs' state to a file and used to later restore that state.
    
    @todo: Add additional validation of parameters read from the config file
    '''

    def __init__(self, **params):
        '''
        Parses a configuration file and any additional keyword
        parameters to create and initialize a new configuration object. 
        
        The __init__ method accepts a list of optional keyword arguments,
        reads in additional arguments from a configuration file, and also
        contains a list of default parameter values. The final value of
        a particular parameter is set to (in order of precedence):
        
          1. The supplied keyword parameter, if one is given
          2. The supplied value in the configuration file, if one is given
          3. The built-in default value (if one exists for this parameter)
        
        The initialization process does not use the logging system like the
        rest of Morpher, since the logging system is dependent on 
        configuration information supplied here.
        
        Refer to the documentation for L{ConfigParser} for information on
        how config files are parsed and how key-value pairs can be read
        and written.
        
        @note: Config defines the default option "basedir" as the path
               to the current working directory. Entries in the config file
               can use this option to refer to other directories relative
               to the current directory, for example: %(BASEDIR)s\data
        
        @raise Exception: An exception is raised if a needed parameter is not
                          found in the params, config file, or default values.
        
        @param params: Override values for optional keyword arguments
        @type params: keyword options
        
        @keyword configfile: The path to the configuration file
        @keyword debug: A boolean value enabling debug mode if I{True}
        @keyword dll: The path to the target dll (no default)
        @keyword listfile: The path to the collection listfile (no default)
        '''
        ConfigParser.ConfigParser.__init__(self)
        
        # Get settings from config file
        # defined variables that can be used by config.ini
        
        defaults = {
                    "configfile" : "config.ini",
                    "debug" : False
                    }
        
        # Set special default values for INI entries
        self.set("DEFAULT", "basedir", os.getcwd())
        
        # Create the 'temp' section for volatile data
        self.add_section('TEMP')
        
        # Read the config file
        cfgfile = params.get("configfile", defaults["configfile"])
        self.read(cfgfile)
        
        # Add some more information
        
        # Is debug mode on?
        debug = params.get("debug", defaults["debug"]) or \
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
        Returns a pretty-printed string suitable for displaying or
        logging the contents of this Config object
                  
        Returns a string similar to the following::
        
            Configuration dump: 
            [TEMP]
              basedir : C:\Users\Rob\workspace\ApiFuzzing
            [directories]
              basedir : C:\Users\Rob\workspace\ApiFuzzing
              data : C:\Users\Rob\workspace\ApiFuzzing\data
              tools : C:\Users\Rob\workspace\ApiFuzzing\tools
              logs : C:\Users\Rob\workspace\ApiFuzzing\logs
            [logging]
              basedir : C:\Users\Rob\workspace\ApiFuzzing
              enabled : yes
              level : debug
        
        @return: Nicely-formatted string containing contents of the Config object
        @rtype: string
        '''
        cfgstr = "\n\n\tConfiguration dump: \n"
        for section in self.sections() :
            cfgstr += "\t[%s]\n" %  section
            for (opt, val) in self.items(section) :
                cfgstr += "\t  %s : %s\n" % (opt, val)
        return cfgstr

        
    