'''
Contains the L{StatusReporter} class definition for reporting
progress updates

@author: Rob Waaser
@contact: robwaaser@gmail.com
@organization: Carnegie Mellon University
@since: November 1, 2011
'''
import sys
import time

class StatusReporter(object):
    '''
    Used for displaying a status bar and dynamically updating it
    on the command line
    
    Tracks program progress by keeping an internal counter that can be 
    incremented by the user, and displays an equivalent status bar and
    estimated completion time on the command line. When an instance is 
    created the user specifies how many "events" must be completed before
    the program is considered to have finished. The user can then
    update the number of "events completed" frequently as the program runs,
    and the status bar will be dynamically updated on the command line
    along with an estimated completion time, calculated based on the number 
    of events completed so far, the elapsed time, and the number of events
    left to complete.
    
    StatusReporter objects can also be reused multiple times by using the
    L{start} method, which essentially resets the counter.
    
    @warning: The status bar assumes that no other output is sent to 
              the console in dynamic update mode and will not display
              correctly otherwise
    
    @ivar estimate: Boolean determining if the estimated time remaining should
                    be displayed along with the status bar
    @ivar dynamic: Boolean determining if the status bar should be erased and
                   reprinted on the console instead of printed on a new line
                   for each update
    @ivar total: The total number of events the statusbar is tracking
    @ivar size: The number of units in the displayed status bar
    @ivar events: The total number of events that have occurred
    @ivar current: The number of units to display in the status bar
    @ivar starttime: The time that the L{start} method was called
    @ivar maxlen: The maximum length that the status bar can print on a line
    @ivar sym: The currently displayed "spinner" symbol
    
    @see: L{SectionReporter} extends this class with additional capability
    '''

    def __init__(self, total=100, size=20, dynamic=True, estimate=True):
        '''
        Initializes a new object with the given settings which can be reused 
        multiple times for printing status bars.
        
        @param total: The total number of events that need to be completed,
                      default is 100
        @type total: integer
        
        @param size: The number of units in the displayed status bar, 
                     default is 20
        @type size: integer
        
        @param dynamic: Enables dynamic updating of the same displayed
                        status bar instead of reprinting on a new line,
                        default is I{True}
        @type dynamic: boolean
        
        @param estimate: Enables displaying the estimated time remaining,
                         default is I{True}
        @type estimate: boolean
        '''
        # Boolean enabling estimate display
        self.estimate = estimate
        # Boolean enabling dynamic update
        self.dynamic = dynamic
        # The total number of events to track
        self.total = total
        # Total number of units the status bar can hold
        self.size = 20
        # The number of events completed so far
        self.events = None
        # Number of units currently displayed in the status bar
        self.current = None
        # The time at which the start method was last called
        self.starttime = None
        # The maximum length the estimate can take up
        self.maxlen = len(" Estimated 000 hr 00 min 00 sec remaining... ")
        # The currently displayed symbol
        self.sym = "-"
        
    def start(self, msg="  Status:"):
        '''
        Resets the internal counters, prints a message, and prints the 
        empty status bar. 
                  
        @note: The elapsed time is calculated from the last time this method
               was called for this object
        @param msg: The message to print just above the status bar, default
                    is "Status:"
        @type msg: string
        '''
        print msg
        self.events = 0
        self.current = 0
        self.starttime = time.time()
        self.sym = "-"
        bar = "  " + self.sym + " [" + " " * (self.size) + "]   0% "
        if self.dynamic :
            newline = "\r"
        else :
            newline = "\n"
        sys.stdout.write(newline + bar)
        
    def pulse(self, events=1):
        '''
        Increments the number of events completed by the given amount, or 1
        by default, then reprints the status bar. 
                  
        @param events: The amount to increment the completed events by, default
                       is 1
        @type events: integer
        '''
        if (self.events == self.total) :
            return
        
        self.events += events
        if self.events > self.total :
            self.events = self.total

        self.printBar()
        
    def correct(self, events):
        '''
        Sets the number of completed events to the given number
                  
        @param events: The number to set the completed event counter to
        @type events: integer
        '''
        self.events = events
        if self.events > self.total :
            self.events = self.total
        
        self.printBar()
            
    def done(self):
        '''
        Triggers immediate completion for this status bar, just as if all
        the events had completed normally
        '''
        num = self.total - self.events
        self.pulse(num)
        
    def printBar(self):
        '''
        Formats and prints the status bar to stdout.
        
        When displayed the status bar should appear similar to::
        
            Status:
            \ [====          ]  25% Estimated  1 min 30 sec remaining.....
            
        If dynamic updating is set, the last line is erased and rewritten
        each time the bar is updated; otherwise it is reprinted on the
        next line.
        '''
        # Create the progress bar
        self.current = (self.events * self.size) / self.total
        
        # Advance the spinner - don't print if we're done
        if self.events == self.total :
            sym = " "
        else :
            self._advanceSym()
            sym = self.sym
        
        bar = "  " + sym + " [" + "=" * self.current + " " * (self.size - self.current) + "]"
        
        # Create the percentage completion display
        percent = " %3d%%" % ((self.events*100)/self.total)
        
        # Estimate of time remaining if available
        if self.events == self.total :
            estimated = " Done!" + " " * self.maxlen + "\n"
        elif not self.estimate or self.events == 0 :
            estimated = ""
        else :
            # Try to estimate remaining time
            delta = (time.time() - self.starttime)/self.events
            secondsleft = int(delta*(self.total-self.events))
            # Get hours
            hr = secondsleft/3600
            if hr == 0 :
                hours = ""
            else :
                hours = " %d hr" % hr
            secondsleft -= hr*3600
            # Get minutes
            mins = secondsleft/60
            if mins == 0 :
                minutes = ""
            else :
                minutes = " %d min" % mins
            secondsleft -= mins*60
            # Get seconds
            seconds = " %d sec" % secondsleft
            estimated = " Estimated " + hours + minutes + seconds + " remaining... " 
            estimated += " " * (self.maxlen - len(estimated))
        
        # If dynamic, carriage return lets us overwrite current line on windows
        if self.dynamic :
            newline = "\r"
        else :
            newline = "\n"
        # Write out the bar using stdout.write so we can do carriage return
        sys.stdout.write(newline + bar + percent + estimated)
        
    def _advanceSym(self):
        '''
        Advances the internal "spinner" symbol by one position.
        '''
        if self.sym == "-" :
            self.sym = "\\"
        elif self.sym == "\\" :
            self.sym = "|"
        elif self.sym == "|" :
            self.sym = "/"
        else :
            self.sym = "-"
