'''
Created on Oct 22, 2011

@author: Rob
'''
import morpher.misc.config as config
import subprocess
import csv
import os
import sys
import logging

def get_funcs():
    '''
    Runs the dllexp.exe tool to pull the export table from the target DLL.
    Returns a list of (funcname, ordinal, rel_addr) tuples - (string, int, int)
    '''
    log = logging.getLogger(__name__)
    # Retrieve configuration info
    dllpath = config.cfg.get('fuzzer', 'target')
    data = config.cfg.get('directories', 'datadir')
    tools = config.cfg.get('directories', 'tooldir')
    
    outpath = os.path.join(data, 'functions.csv')
    toolpath = os.path.join(tools, 'dllexp.exe')
    
    # Call the dllexp.exe tool on the target DLL
    args = [toolpath, '/from_files', dllpath, '/scomma', outpath]
    log.info("Extracting export table with \"dllexp.exe\"")
    log.debug("Command Line: %s /from_files %s /scomma %s", toolpath, dllpath, outpath)
    ret = subprocess.call(args)
    if ret != 0 :
        log.error("DLL export tool failure. Returned code %d", ret)
        sys.exit()
        
    # Open the CSV output
    try :
        f = open(outpath)
    except :
        log.exception("Can't open the exported CSV file")
        sys.exit()  
    
    # Parse the CSV file
    log.info("Parsing the CSV file written by dllexp.exe")
    filefmt = ['name','addr_abs', 'addr_rel', 'ordinal', 'dll', 'path', 'type']
    result = csv.DictReader(f, filefmt) 
    # Ordinal is printed as '1 (0x1)', so just take first part
    l = [(r['name'], int(r['ordinal'].split()[0]), int(r['addr_rel'], 16)) for r in result]
    f.close()
    
    log.info("Found %d exported function entries", len(l))
    log.debug("Extracted entries: %s", str(l))
        
    return l
    