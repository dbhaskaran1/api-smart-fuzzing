'''
Contains the L{SectionReporter} class definition for reporting
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
    multi-part status bars
    '''

    def __init__(self, numsections):
        '''
        Initializes a new object with the underlying L{StatusReporter} 
        object using default settings
        
        @param numsections: The total number of sections tracked by the status bar
        @type numsections: integer
        '''
        status_reporter.StatusReporter.__init__(self)
        # The total number of sections
        self.numsections = numsections
        # Map of section id -> (current, total)
        self.table = {}
        for i in range(self.numsections) :
            self.table[i] = (0, 1)
            
        self.nextsection = 0
        self.percentage = 0
        
    def getChunk(self, numevents):
        '''
        Sets the current section to the given section number and sets the 
        total number of events tracked by this section
        
        The variable "curevents" is dynamically scaled at this time as if
        all previous sections had also tracked the same number of events
                  
        @param section: The index of the section to start, beginning from 1.
        @type section: integer
        
        @param numevents: Total number of events tracked by this section.
        @type numevents: integer
        '''
        if self.nextsection == self.numsections :
            return None
        
        mysection = self.nextsection
        self.nextsection += 1
        
        self.table[mysection] = (0, numevents)
        return mysection
        
    def pulseChunk(self, section, events=1):
        '''
        Increments the number of events completed by the given amount, or 1
        by default, then reprints the status bar. 
        
        @note: The status bar will not actually reflect this section as being
               100 percent complete until L{endSection} is called.
        
        @param events: The number of events to increment the counter by,
                       default is 1
        @type events: integer
        '''
        (current, maxevents) = self.table[section]
        newtotal = current + events

        if newtotal > maxevents :
            newtotal = maxevents 
        
        self.table[section] = (newtotal, maxevents)
        
        # Calculate new percentage
        old = (current*100)/(maxevents)
        oldtotal = (old)/(self.numsections)
        
        new = (newtotal*100)/(maxevents)
        newtotal = (new)/(self.numsections)
        
        self.percentage += (newtotal - oldtotal)
        
        if self.percentage >= 100 : 
            self.percentage = 99
            
        self.correct(self.percentage)
        
    def endChunk(self, section):
        '''
        Ends the current section, correcting the status bar to reflect
        exactly M{(cursection/numsections)*100} percent completion 
        '''
        (current, total) = self.table[section]
        self.pulseChunk(section, total - current)