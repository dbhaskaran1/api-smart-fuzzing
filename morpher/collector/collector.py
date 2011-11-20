'''
Contains the L{Collector} class for recording DLL function calls by a 
list of programs.

@author: Rob Waaser
@contact: robwaaser@gmail.com
@organization: Carnegie Mellon University
@since: October 23, 2011
'''

import xml.dom.minidom as xml
import trace_recorder
import os
import pickle
import logging
from morpher.misc import status_reporter

class Collector(object):
    '''
    Class documentation
    '''

    def __init__(self, cfg):
        '''
        '''
        # The Config object used for configuration info
        self.cfg = cfg
        # The logging object used for reporting
        self.log = logging.getLogger(__name__)
        # The DLL xml model used for collection
        self.model = None
        # The current trace number
        self.counter = 0
        # The path to the directory for storing traces
        datadir = self.cfg.get('directories', 'data')
        self.tracedir = os.path.join(datadir, 'traces')
        self.modelpath = os.path.join(datadir, 'model.xml')
    
    def collect(self):
        '''
        Top-level collection routine
        '''
        # Check if collecting is enabled
        if not self.cfg.getboolean('collector', 'enabled') : 
            print "  Collector DISABLED\n"
            self.log.info("Collecting is off")
            return
        
        # Clear out or create data/traces
        if os.path.isdir(self.tracedir) :
            for filename in os.listdir(self.tracedir) :
                path = os.path.join(self.tracedir, filename)
                if os.path.isfile(path) and filename.startswith('trace-') and \
                    filename.endswith('.pkl'):
                    os.remove(path)
        else :
            os.mkdir(self.tracedir)
            
        # Get configuration info
        listfile = self.cfg.get('collector', 'list')
        
        # Get the XML model
        self.log.info("Reading the model.xml file")
        try :
            f = open(self.modelpath)
        except :
            msg = "Could not open model file %s" 
            self.log.exception(msg, self.modelpath)
            raise Exception(msg % self.modelpath)
        self.model = xml.parse(f).getElementsByTagName("dll")[0]
        f.close()
        
        recorder = trace_recorder.TraceRecorder(self.cfg, self.model)
        
        # Get the collection list
        self.log.info("Reading the collection list")
        try :
            f = open(listfile)
        except :
            msg = "Could not open collection list %s"
            self.log.exception(msg, listfile)
            raise Exception(msg % listfile)
        lines = []
        for line in f :
            lines.append(line)
        f.close()
        
        self.log.info("Beginning collection process")
        sr = status_reporter.StatusReporter(total=len(lines))
        sr.start("  Collector is running...")
        self.counter = 0
        for line in lines :
            # Record this trace
            (exe,args) = self.parseline(line)
            if exe == None :
                self.log.warning("Couldn't parse collection line: %s", line)
                continue
            trace = recorder.record(exe, args)
            if trace != None :
                # Dump to a new tracefile
                tracepath = os.path.join(self.tracedir, 'trace-%d.pkl' % self.counter)
                try :
                    tracefile = open(tracepath, "wb")
                except :
                    self.log.warning("Couldn't open file for storing trace: %s", tracepath)
                    continue
                self.log.info("Creating trace file %s", tracepath)
                pickle.dump(trace, tracefile)
                tracefile.close()
                self.counter += 1
            sr.pulse()
        
        self.log.info("Collection process complete")
      
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
                    args += strings[j] + " "
                return (exepath, args)
        # Couldn't parse the command line  
        return (None, None)
        