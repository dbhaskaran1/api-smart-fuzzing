'''
Created on Oct 21, 2011

@author: Rob
'''
import xml.dom.minidom as xml
import logging
import os
import dllexp
from morpher.misc import status_reporter

class Parser(object):
    '''
    Parser documentation
    '''

    def __init__ (self, cfg):
        '''
        init documentation
        '''
        # The Config object used for configuration info
        self.cfg = cfg
        # The logging object used for reporting
        self.log = logging.getLogger(__name__)
        # The dllexp.exe wrapper object for getting export data
        self.dllexp = dllexp.DllExp(cfg)
        
    def parse(self):
        '''
        Analyzes the target DLL and header file to retrieve function prototypes.
        Outputs a XML file containing a model of the exported prototypes
        '''
        # Get relevant configuration information
        datadir = self.cfg.get('directories', 'data')
        modelpath = os.path.join(datadir, 'model.xml')
        
        # Check if parsing is enabled
        if not self.cfg.getboolean('parser', 'enabled') : 
            self.log.info("Parsing is disabled")
            print "  Parser DISABLED\n"
            return
            
        sr = status_reporter.StatusReporter(total=2)
        sr.start("  Parser is running...")
        # Parsing is enabled
        self.log.info("Beginning parse routine")
        
        # Retrieve the export table from the DLL
        exportlist = self.dllexp.getFunctions()
        sr.pulse()
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
        if self.log.isEnabledFor(logging.DEBUG) :
            xmlstr = top.toprettyxml(indent="    ", newl="\n")
            self.log.debug("\n\nXML Tree:\n%s\n", xmlstr)
        try :
            f = open(modelpath, mode="w")
        except :
            msg = "Couldn't open %s"
            self.log.exception(msg, modelpath)
            raise Exception(msg % modelpath)
        top.writexml(f, addindent="    ", newl="\n")
        f.close()
        sr.pulse()

    