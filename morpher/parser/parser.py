'''
Created on Oct 21, 2011

@author: Rob
'''
import xml.dom.minidom as xml
import subprocess
import logging
import os
import csv

class Parser:
    
    cfg = None
    log = None
    
    def __init__ (self, cfg):
        self.cfg = cfg
        self.log = cfg.getLogger(__name__)
        
    def parse(self):
        '''
        Analyzes the target DLL and header file to retrieve function prototypes.
        Outputs a XML file containing a model of the exported prototypes
        '''
        
        # Get relevant configuration information
        modelfile = self.cfg.get('output', 'modelfile')
        
        # Check if parsing is enabled
        if not self.cfg.getboolean('parser', 'parsing') : 
            # Check that model already exists
            self.log.info("Parsing is off, using existing model.xml")
            if not os.path.exists(modelfile) :
                msg = "Model file does not exist"
                self.log.error(msg)
                raise Exception(msg)
            else :
                return
        
        # Parsing is enabled
        self.log.info("Beginning parse routine")
        
        # Retrieve the export table from the DLL
        exportlist = self.getFunctions()
    
        # INSERT ADDITIONAL PARSING LOGIC HERE
        # Right now all this does is read the export 
        # table of the DLL and write out that information
        # in XML format
    
        # Create the XML tree    
        self.log.info("Creating the XML model")
        doc = xml.getDOMImplementation().createDocument(None, "dll", None)
        top = doc.documentElement
        
        # Add function nodes
        for (fname, ordinal, addr) in exportlist :
            func = doc.createElement("function")
            func.setAttribute("name", fname)
            func.setAttribute("ordinal", str(ordinal))
            func.setAttribute("address", str(addr))
            top.appendChild(func)
            
        # Write out the model file
        self.log.info("Writing XML tree to model file")
        if self.cfg.logLevel() == logging.DEBUG :
            xmlstr = top.toprettyxml(indent="    ", newl="\n")
            self.log.debug("\n\nXML Tree:\n%s\n", xmlstr)
        try :
            f = open(modelfile, mode="w")
        except :
            msg = "Couldn't open %s"
            self.log.exception(msg, modelfile)
            raise Exception(msg % modelfile)
        top.writexml(f, addindent="    ", newl="\n")
        f.close()

    def getFunctions(self):
        '''
        Runs the dllexp.exe tool to pull the export table from the target DLL.
        Returns a list of (funcname, ordinal, rel_addr) tuples - (string, int, int)
        '''
        # Retrieve configuration info
        dllpath = self.cfg.get('fuzzer', 'target')
        data = self.cfg.get('directories', 'datadir')
        tools = self.cfg.get('directories', 'tooldir')
        
        outpath = os.path.join(data, 'functions.csv')
        toolpath = os.path.join(tools, 'dllexp.exe')
        
        # Call the dllexp.exe tool on the target DLL
        args = [toolpath, '/from_files', dllpath, '/scomma', outpath]
        self.log.info("Extracting export table with \"dllexp.exe\"")
        self.log.debug("Command Line: %s /from_files %s /scomma %s", toolpath, dllpath, outpath)
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