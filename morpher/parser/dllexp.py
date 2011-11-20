'''
Created on Oct 25, 2011

@author: Rob
'''
import subprocess
import os
import csv
import logging

class DllExp(object):
    '''
    Acts as a front-end to call the DLL Explorer (dllexp.exe) tool
    '''

    def __init__ (self, cfg):
        '''
        init documentation
        '''
        # The Config object used for configuration info
        self.cfg = cfg
        # The logging object used for reporting
        self.log = logging.getLogger(__name__)
        tools = self.cfg.get('directories', 'tools')
        # The path to the dllexp.exe tool
        self.toolpath = os.path.join(tools, 'dllexp.exe')
        
    def getFunctions(self):
        '''
        Runs the dllexp.exe tool to pull the export table from the target DLL.
        Returns a list of (funcname, ordinal, rel_addr) tuples - (string, int, int)
        '''
        # Retrieve configuration info
        dllpath = self.cfg.get('fuzzer', 'target')
        data = self.cfg.get('directories', 'data')
        outpath = os.path.join(data, 'functions.csv')
        
        
        # Call the dllexp.exe tool on the target DLL
        args = [self.toolpath, '/from_files', dllpath, '/scomma', outpath]
        self.log.info("Extracting export table with \"dllexp.exe\"")
        self.log.debug("Command Line: %s /from_files %s /scomma %s", self.toolpath, dllpath, outpath)
        ret = subprocess.call(args)
        if ret != 0 :
            msg = "DLL export tool failure. Returned code %d"
            self.log.error(msg, ret)
            raise Exception(msg % ret)
            
        # Open the CSV output
        try :
            f = open(outpath)
        except :
            msg = "Can't open the exported CSV file"
            self.log.exception(msg)
            raise Exception(msg)
        
        # Parse the CSV file
        self.log.info("Parsing the CSV file written by dllexp.exe")
        filefmt = ['name','addr_abs', 'addr_rel', 'ordinal', 'dll', 'path', 'type']
        result = csv.DictReader(f, filefmt) 
        # Ordinal is printed as '1 (0x1)', so just take first part
        l = [(r['name'], int(r['ordinal'].split()[0]), int(r['addr_rel'], 16)) for r in result]
        f.close()
        
        self.log.info("Found %d exported function entries", len(l))
        self.log.debug("Extracted entries: %s", str(l))
        
        return l