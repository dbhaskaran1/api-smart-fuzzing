'''
Created on Oct 21, 2011

@author: Rob
'''
import xml.dom.minidom as xml
import logging
import os
import dllexp

class Parser(object):
    '''
    Parser documentation
    '''
    
    # The Config object used for configuration info
    cfg = None
    
    # The logging object used for reporting
    log = None
    
    # The dllexp.exe wrapper object for getting export data
    dllexp = None
    
    def __init__ (self, cfg):
        '''
        init documentation
        '''
        self.cfg = cfg
        self.log = cfg.getLogger(__name__)
        self.dllexp = dllexp.DllExp(cfg)
        
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
        exportlist = self.dllexp.getFunctions()
    
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

    