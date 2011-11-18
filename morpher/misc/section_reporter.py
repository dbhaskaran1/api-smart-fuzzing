'''
Contains the L{SectionReporter} class definition for reporting
progress updates

@author: Rob Waaser
@contact: robwaaser@gmail.com
@organization: Carnegie Mellon University
@since: November 2, 2011
'''
import status_reporter

class SectionReporter(status_reporter.StatusReporter):
    '''
    Extends L{StatusReporter} with additional functionality for 
    multi-part status bars
    
    L{StatusReporter} requires that you know the number of events that 
    will be tracked at the time the status bar is created. However in
    some cases this information is not completely known. For example, a
    program might be written to process ten batches of files, but the number
    of files in the each batch is not known until the previous batch is
    completed. SectionReporter allows the status bar to be divided into
    a known number of sections, but the number of events tracked in each
    section does not need to be known until that section is reached by
    the status bar. This allows the status bar to display quasi-accurate 
    completion information and remaining time estimates even if the actual
    information is impossible to determine at that time.
    
    SectionReporter objects can also be reused multiple times by using the
    L{start} method, which essentially resets the counter. The usage pattern
    is::
        rep = SectionReporter(2)
        rep.start()
        rep.startSection(1, 10)
        ...call rep.pulse() ten times....
        rep.endSection()
        rep.startSection(2, 3)
        ...call rep.pulse() three times
        rep.endSection()
    
    @warning: The status bar assumes that no other output is sent to 
              the console in dynamic update mode and will not display
              correctly otherwise
    
    @ivar numsections: The total number of sections making up the status bar
    @ivar cursection: The current section index, starting from 1
    @ivar curtotal: The total number of events tracked by the current section
    @ivar curevents: The total number of events that have completed, across all
                     sections - dynamically scaled when a new section is entered
                     as if all previous sections were composed of the same number
                     of total events
    
    @see: L{StatusReporter} is the base class for this class
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
        # The index of the current section, starting at 1
        self.cursection = None
        # The total number of events tracked by the current section
        self.curtotal = None
        # The current number of completed events, across all sections
        self.curevents = None
        
    def startSection(self, section, numevents):
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
        self.cursection = section
        self.curtotal = numevents
        self.curevents = (self.cursection - 1)*numevents
        
    def pulse(self, events=1):
        '''
        Increments the number of events completed by the given amount, or 1
        by default, then reprints the status bar. 
        
        @note: The status bar will not actually reflect this section as being
               100 percent complete until L{endSection} is called.
        
        @param events: The number of events to increment the counter by,
                       default is 1
        @type events: integer
        '''
        self.curevents += events
        percent = (self.curevents*100)/(self.numsections*self.curtotal)
        if percent >= 100 : 
            percent = 99
        maxpercent = (self.cursection*100)/self.numsections
        if percent >= maxpercent :
            percent = maxpercent
        self.correct(percent)
        
    def endSection(self):
        '''
        Ends the current section, correcting the status bar to reflect
        exactly M{(cursection/numsections)*100} percent completion 
        '''
        if self.cursection == self.numsections :
            self.done()
        else :
            percent = (self.cursection*100)/self.numsections
            self.correct(percent)