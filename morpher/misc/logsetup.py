'''
Created on Nov 1, 2011

@author: Rob
'''
import logging
import atexit
import sys
import os

def setupLogging(cfg, root=None):
    '''
    setup method documentation
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
        
    # What's the log level
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
    Takes a string and turns it into matching logging level
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