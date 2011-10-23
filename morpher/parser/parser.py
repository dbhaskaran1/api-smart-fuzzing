'''
Created on Oct 21, 2011

@author: Rob
'''
import xml.dom.minidom as xml
import funcs
import logging
import os
import sys
import morpher.misc.config as config

def parse():
    '''
    Analyzes the target DLL and header file to retrieve function prototypes.
    Outputs a XML file containing a model of the exported prototypes
    '''
    log = logging.getLogger(__name__)
    
    # Get relevant configuration information
    datadir = config.cfg.get('directories', 'datadir')
    modelfile = os.path.join(datadir, 'model.xml')
    
    # Check if parsing is enabled
    if not config.cfg.get('parser', 'parsing') : 
        # Check that model already exists
        log.info("Parsing is off, using existing model.xml")
        if not os.path.exists(modelfile) :
            log.error("Model file does not exist")
            sys.exit()
        else :
            return
    
    # Parsing is enabled
    log.info("Beginning parse routine")
    
    # Retrieve the export table from the DLL
    exportlist = funcs.get_funcs()

    # INSERT ADDITIONAL PARSING LOGIC HERE
    # Right now all this does is read the export 
    # table of the DLL and write out that information
    # in XML format

    # Create the XML tree    
    log.info("Creating the XML model")
    doc = xml.getDOMImplementation().createDocument(None, "dll", None)
    top = doc.documentElement
    
    # Add function nodes
    for (fname, ordinal, addr) in exportlist :
        func = doc.createElement("function")
        func.setAttribute("name", fname)
        func.setAttribute("ordinal", ordinal)
        func.setAttribute("address", addr)
        top.appendChild(func)
        
    # Write out the model file
    log.info("Writing XML tree to model.xml")
    f = open(modelfile, mode="w")
    top.writexml(f, addindent="    ", newl="\n")
        
        