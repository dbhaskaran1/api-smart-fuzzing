'''
Contains the L{DllExp} class which is a python wrapper
for the external DllExplorer Tool.

@author: Erik Schmidt
@contact: emschmitty@gmail.com
@organization: Carnegie Mellon University
@since: October 23, 2011
'''
import subprocess
import os
import csv
import logging

class DllExp(object):
    '''
    Class documentation
    
    @ivar cfg: The L{Config} object
    @ivar log: The L{logging} object
    '''

    def __init__ (self, cfg):
        '''
        Stores the configuration object and initializes the internal data
        
        @param cfg: The configuration object to use
        @type cfg: L{Config} object
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
        Generates a list of exported functions from the target DLL using the 
        DllExplorer tool.
        
        This function calls an instance of DllExplorer, which output a list of 
        function definitions to a .csv file. It then opens and parses the file, 
        adding the information to an array of string which is then returned to 
        calling function.
        
        @return: An array of exported function names
        @rtype: string array
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
        # Grab the name and add it to the array
        l = [(r['name']) for r in result]

        f.close()
        
        self.log.info("Found %d exported function entries", len(l))
        self.log.debug("Extracted entries: %s", str(l))
        
        return l