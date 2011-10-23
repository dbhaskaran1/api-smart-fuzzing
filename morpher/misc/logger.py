'''
Created on Oct 22, 2011

@author: Rob
'''
import logging
import sys
import os
import atexit

def setup():
    '''
    Initialize the logging system
    '''
    # setup message format
    fmt = logging.Formatter("%(levelname)-10s %(asctime)s %(message)s")
    
    # Create a handler to print CRITICAL messages to stderr
    crit_hand = logging.StreamHandler(sys.stderr)
    crit_hand.setLevel(logging.CRITICAL)
    crit_hand.setFormatter(fmt)
    
    # Create handler that prints to a file
    main_hand = logging.FileHandler(os.path.join(logdir, 'main.log'))
    main_hand.setFormatter(fmt)
    
    # Create top-level logger "main"
    main_log = logging.getLogger("main")
    main_log.setLevel(logging.INFO)
    main_log.addHandler(main_hand)
    main_log.addHandler(crit_hand)
    
    atexit.register(logging.shutdown)
    