'''
Contains the L{ParallelReporter} class definition for reporting
progress updates

@author: Rob Waaser
@contact: robwaaser@gmail.com
@organization: Carnegie Mellon University
@since: December 7, 2011
'''
import status_reporter

class ParallelReporter(status_reporter.StatusReporter):
    '''
    Extends L{StatusReporter} with additional functionality for 
    multi-part status bars, where the status bar reflects the
    total completion across a set of individual "chunks". The 
    intention is to report the status in an environment where
    work is being done in parallel or out-of-order and the
    total amount of work is unknown at initialization.
    
    @ivar numchunks: The number of chunks tracked by this status bar
    @ivar table: Map tracking completion for each chunk
    @ivar nextchunk: The next available chunk id
    @ivar percentage: The total percentage completed across all chunks
    '''

    def __init__(self, numchunks):
        '''
        Initializes a new object with the underlying L{StatusReporter} 
        object using default settings
        
        @param numchunks: The total number of chunks tracked by the status bar
        @type numchunks: integer
        '''
        status_reporter.StatusReporter.__init__(self)
        # The total number of sections
        self.numchunks = numchunks
        # Map of section id -> (current, total)
        self.table = {}
        for i in range(self.numchunks) :
            self.table[i] = (0, 1)
        # The next section id to be distributed  
        self.nextchunk = 0
        # The total percentage completed so far
        self.percentage = 0
        
    def getChunk(self, numevents):
        '''
        Get the next available chunk id. The worker calling this function
        should use the chunk id to update the chunk's progress in future
        calls to this ParallelReporter.
        
        @param numevents: Total number of events tracked by this chunk.
        @type numevents: integer
        
        @return: The id of the next available chunk
        @rtype: integer
        '''
        if self.nextchunk == self.numchunks :
            return None
        
        mychunk = self.nextchunk
        self.nextchunk += 1
        
        self.table[mychunk] = (0, numevents)
        return mychunk
        
    def pulseChunk(self, chunk, events=1):
        '''
        Increments the number of events completed for the given chunk by
        the given amount, or by 1 if the number of events is not specified
        
        @note: The status bar will not actually reflect this chunk as being
               100 percent complete until L{endChunk} is called.
        
        @param events: The number of events to increment the counter by,
                       default is 1
        @type events: integer
        '''
        (current, maxevents) = self.table[chunk]
        newtotal = current + events

        if newtotal > maxevents :
            newtotal = maxevents 
        
        self.table[chunk] = (newtotal, maxevents)
        
        # Calculate new percentage
        old = (current*100)/(maxevents)
        oldtotal = (old)/(self.numsections)
        
        new = (newtotal*100)/(maxevents)
        newtotal = (new)/(self.numsections)
        
        self.percentage += (newtotal - oldtotal)
        
        if self.percentage >= 100 : 
            self.percentage = 99
            
        self.correct(self.percentage)
        
    def endChunk(self, chunk):
        '''
        Ends this section, setting this section to be 100% complete
        and updating the status bar to reflect that.
        
        @param section: The chunk id to finish
        @type section: integer
        '''
        (current, total) = self.table[chunk]
        self.pulseChunk(chunk, total - current)