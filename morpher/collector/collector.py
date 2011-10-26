'''
Created on Oct 23, 2011

@author: Rob
'''
import logging
import xml.dom.minidom as xml
from morpher.pydbg import pydbg
from morpher.pydbg import defines
from morpher.misc import config
import struct
import sys
import os

class Collector(object):
    '''
    Class documentation
    '''

    # The Config object used for configuration info
    cfg = None
    
    # The logging object used for reporting
    log = None

    def __init__(self, cfg):
        self.cfg = cfg
        self.log = cfg.getLogger(__name__)
    model = None
    counter = 0
    recordfile = None
    log = None
    
    def collect(self):
        '''
        Top-level collection routine
        '''
        global model
        global log
        log = logging.getLogger(__name__)
        # Get configuration info
        modelfile = config.cfg.get('output', 'modelfile')
        listfile = config.cfg.get('collector', 'listfile')
        
        # Get the XML model
        log.info("Reading the model.xml file")
        try :
            f = open(modelfile)
        except :
            log.exception("Could not open model file %s", modelfile)
            sys.exit()
        model = xml.parse(f).getElementsByTagName("dll")[0]
        f.close()
        
        # Get the collection list
        log.info("Reading the collection list")
        try :
            f = open(listfile)
        except :
            log.exception("Could not open collection list %s", listfile)
            sys.exit()
        
        log.info("Beginning collection process")
        global counter
        counter = 0
        for line in f :
            record(line)
        
        f.close()
        
    def record(self,line):
        '''
        Given an application that uses the target DLL and an XML
        model tree, 
        '''
        global model
        global counter
        global recordfile
        global log
        # Get config info
        # dll = config.cfg.get('fuzzer', 'target')
        # parse the command line
        (exe, arg) = parseline(line)
        if exe == None :
            log.warning("Couldn't parse collection line: %s", line)
            return
        log.info("Running collection line: exe - %s  arg - %s", exe, arg)
        # Create a new run file
        counter += 1
        datadir = config.cfg.get('directories', 'datadir')
        loc = os.path.join(datadir, 'run%s.txt' % counter)
        try :
            recordfile = open(loc, "w")
        except :
            log.exception("Couldn't open file %s", loc)
            return
        log.info("Created run file %s", loc)
        # Load the application in a debugger
        log.info("Loaded program, setting breakpoints")
        dbg = pydbg.pydbg()
        dbg.load(exe, command_line=arg)
        # Set breakpoints on functions
        dbg.set_callback(defines.LOAD_DLL_DEBUG_EVENT, load_handler)
        
            
        log.info("Running the program")
        dbg.run()
        
    def load_handler(self,dbg):
        global model
        global log
        last_dll = dbg.get_system_dll(-1)
        print "loading:%s from %s into:%08x size:%d" % (last_dll.name, last_dll.path, last_dll.base, last_dll.size)
        if last_dll.name == "libTestDLL.dll" :
            for node in model.getElementsByTagName("function") :
                ordinal = str(node.getAttribute("name"))
                address = dbg.func_resolve('libTestDLL.dll', ordinal)
                print ordinal
                print address
                log.debug("Setting breakpoint: dll %s ordinal %s address %x", "libTestDLL", ordinal, address)
                desc = "Ordinal %s" % ordinal
                dbg.bp_set(address, description=desc, handler=func_handler)
                log.debug("Breakpoint set at address %x", address)
        
        return defines.DBG_CONTINUE     # or other continue status
        
    def func_handler(self,dbg):
        global recordfile
        global log
        log.debug("Breakpoint tripped, address %x", dbg.context.Eip)
        addr = dbg.context.Esp + 0x4
        param1 = dbg.read_process_memory(addr, 4)
        param1 = int(struct.unpack("L",param1)[0])
        recordfile.write(str(param1) + "\n")
        log.debug("Writing value to dump file: %d", param1)
        return defines.DBG_CONTINUE 
      
    def parseline(self,line):
        '''
        Given a command line string, returns a pair of strings (pathtoexe, args)
        Returns (none, none) if the line couldn't be parsed
        '''
        strings = line.split()
        # Keep adding tokens until we have a string that is an actual path
        exepath = ""
        for i in range(0, len(strings)) :
            exepath += strings[i]
            if os.path.isfile(exepath) :
                # Concatenate the remaining tokens and return as arg string
                args = ""
                for j in range(i + 1, len(strings)) :
                    args += strings[j]
                return (exepath, args)
            
        return (None, None)
        