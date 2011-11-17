'''
Contains the L{setupLogging} and L{translateLevel}
function definitions, used for interacting with 
the standard Python L{logging} module

@author: Rob Waaser
@contact: robwaaser@gmail.com
@organization: Carnegie Mellon University
@since: November 1, 2011
'''
import logging
import atexit
import sys
import os

def setupLogging(cfg, root=None):
    '''
    When called with a Config object, uses the Config object to
    extract configuration information and sets up Python's standard
    L{logging} system for project-wide use.
    
    Initializes the log system provided by Python's L{logging} module using
    information in a provided L{Config} object. The log system defines the
    top-level package in the heirarchy of this module as the root logger by
    default, or a supplied root can be used instead.
    
    The following actions are performed:
    
      - The logging->enabled option in the cfg object is checked and used to
       either enable or disable logging globally
      - Sets up a handler that prints logging messages of level logging.ERROR
       or higher to standard output
      - Sets up a handler that prints all other logging messages to a log file,
       located in the directory specified in directories->logging
      - Stops propagation of messages above the defined root logger
      - Registers an L{atexit} handler that ensures the logging system is 
       properly flushed upon program exit.
       
    @requires: cfg must specify the logging->enabled option
    @requires: If logging->enabled is I{True}, cfg must specify:
                  - the logging->level option
                  - the directories->logs option
                  
    @param cfg: A L{Config} object containing logging setup information
    @type cfg: L{Config} object
    @param root: An optional string specifying the name of the root module
    @type root: string
    '''
    # Figure out the root of the hierarchy
    if root == None :
        root = __name__.split(".")[0]
    else :
        root = root
    
    # Is logging on, if not disable globally
    enabled = cfg.getboolean('logging', 'enabled')
    if not enabled :
        logging.disable(logging.CRITICAL)
        return
    else :
        logging.disable(logging.NOTSET)
        
    # What's the log level?
    string = cfg.get('logging', 'level')
    level = translateLevel(string)
    
    # Format of all our log messages
    fmt = logging.Formatter("%(levelname)-10s %(name)-10s %(asctime)s %(message)s")
    
    # Set up handler to print all error messages or above to console
    err_hand = logging.StreamHandler(sys.stderr)
    err_hand.setLevel(logging.ERROR)
    err_hand.setFormatter(fmt)
    
    # Figure out log file path and remove it if it already exists
    logdir = cfg.get('directories', 'logs')
    path = os.path.join(logdir, root + ".log")
    if os.path.isfile(path) :
        os.remove(path)
        
    # Create a handler to log all messages to a file
    file_hand = logging.FileHandler(path)
    file_hand.setFormatter(fmt)
    
    # Set up the root logger
    logger = logging.getLogger(root)
    logger.propagate = False
    logger.setLevel(level)
    logger.addHandler(file_hand)
    logger.addHandler(err_hand)
    
    # Make sure that logs are flushed on exit 
    atexit.register(logging.shutdown)
    
    log = logging.getLogger(__name__)
    levelstr = cfg.get('logging', 'level')
    log.info("Logging system initialized, log level: %s", levelstr)
    
def translateLevel(string):
    '''
    @summary: Takes a string and turns it into matching L{logging} level
    
    Utility method with returns the following values for the given string:
    
      - 'debug' S{rarr} logging.DEBUG
      - 'info' S{rarr} logging.INFO
      - 'warning' S{rarr} logging.WARNING
      - 'error' S{rarr} logging.ERROR
      - 'critical' S{rarr} logging.CRITICAL
      
    An exception is raised if no match is found for the given string

    @note: The given string is converted to lowercase and L{strip} is applied
           before any comparisons
           
    @raise Exception: Throw an exception if the given string is not matched
           
    @param string: The string to translate to a logging level
    @type string: string
    
    @return: A corresponding constant from the L{logging} module
    @rtype: integer
    '''
    levelstr = string.strip().lower()
    if levelstr == 'debug' :
        level = logging.DEBUG
    elif levelstr == "info" :
        level = logging.INFO
    elif levelstr == "warning" :
        level = logging.WARNING
    elif levelstr == "error" :
        level = logging.ERROR
    elif levelstr == "critical" :
        level = logging.CRITICAL
    else :
        raise Exception("%s is not a valid logging level", levelstr)
    return level