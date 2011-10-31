'''
Created on Oct 23, 2011

@author: Rob
'''
import xml.dom.minidom as xml
import trace_recorder
import os
import pickle

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
        self.log = cfg.getLogger(__name__)
        # The DLL xml model used for collection
        self.model = None
        # The current trace number
        self.counter = 0
        # The path to the directory for storing traces
        datadir = self.cfg.get('directories', 'datadir')
        self.tracedir = os.path.join(datadir, 'traces')
        # Clear out or create data/traces
        if os.path.isdir(self.tracedir) :
            for filename in os.listdir(self.tracedir) :
                path = os.path.join(self.tracedir, filename)
                if os.path.isfile(path) and filename.startswith('trace-') and \
                    filename.endswith('.pkl'):
                    os.remove(path)
        else :
            os.mkdir(self.tracedir)
    
    def collect(self):
        '''
        Top-level collection routine
        '''
        # Get configuration info
        modelfile = self.cfg.get('output', 'modelfile')
        listfile = self.cfg.get('collector', 'listfile')
        
        # Get the XML model
        self.log.info("Reading the model.xml file")
        try :
            f = open(modelfile)
        except :
            msg = "Could not open model file %s" 
            self.log.exception(msg, modelfile)
            raise Exception(msg % modelfile)
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
        
        self.log.info("Beginning collection process")
        self.counter = 0
        for line in f :
            # Record this trace
            (exe,args) = self.parseline(line)
            if exe == None :
                self.log.warning("Couldn't parse collection line: %s", line)
                continue
            trace = recorder.record(exe, args)
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
        
        f.close()
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
        