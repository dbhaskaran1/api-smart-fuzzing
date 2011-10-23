'''
Created on Oct 22, 2011

@author: Rob
'''
import logging.handlers
import config
import sys
import os
import atexit

def setup():
    '''
    Initializes the logging system and resets existing logs
    '''
    # Figure out the logging level
    levelstr = config.cfg.get('logging','loglevel').lower().strip()
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
    fmt = logging.Formatter("%(levelname)-10s %(asctime)s %(message)s")
    
    # Create a handler to print ERROR or higher messages to stderr
    err_hand = logging.StreamHandler(sys.stderr)
    err_hand.setLevel(logging.ERROR)
    err_hand.setFormatter(fmt)
    
    # Create handler that prints to a file
    logdir = config.cfg.get('directories','logdir')
    bufsize = config.cfg.get('logging', 'bufsize')
    flush = config.cfg.get('logging','flushlevel')
    
    path = os.path.join(logdir, 'main.log')
    os.remove(path)
    main_f_hand = logging.FileHandler(path)
    main_f_hand.setFormatter(fmt)
    main_hand = logging.handlers.MemoryHandler(bufsize, flush, main_f_hand)
    
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
    log = logging.getLogger(__name__)
    log.info("Logging system initialized, log level: %s", levelstr)
    
def level() :
    '''
    Returns the effective logging.LEVEL object of the root logger
    '''
    log = logging.getLogger("morpher")
    return log.getEffectiveLevel()