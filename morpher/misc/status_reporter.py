'''
Created on Nov 1, 2011

@author: Rob
'''
import sys
import time

class StatusReporter(object):
    '''
    classdocs
    '''

    def __init__(self, total=100, size=20, dynamic=True, estimate=True):
        '''
        Constructor
        '''
        self.estimate = estimate
        self.dynamic = dynamic
        self.total = total
        self.size = 20
        self.events = None
        self.current = None
        self.starttime = None
        self.curtime = None
        self.maxlen = len(" Estimated 000 hr 00 min 00 sec remaining... ")
        
    def start(self, msg="Status:"):
        '''
        Reset the internal counter, print a message, and
        print the status bar. 
        '''
        print msg
        self.events = 0
        self.current = 0
        self.starttime = time.time()
        bar = "  [" + " " * (self.size) + "]   0% "
        if self.dynamic :
            newline = "\r"
        else :
            newline = "\n"
        sys.stdout.write(newline + bar)
        
    def pulse(self, events=1):
        '''
        Increments the number of events occurred so far by the number
        specified, or 1 by default. Prints the bar again
        '''
        if (self.events == self.total) :
            return
        
        self.events += events
        if self.events > self.total :
            self.events = self.total

        self.printBar()
        
    def correct(self, events):
        '''
        Can force the number of events seen so far to equal given number
        '''
        self.events = events
        if self.events > self.total :
            self.events = self.total
        
        self.printBar()
            
    def done(self):
        '''
        Forces the total number of events to equal the threshold as if
        the events had accumulated normally
        '''
        num = self.total - self.events
        self.pulse(num)
        
    def printBar(self):
        '''
        Formats and prints the bar to stdout to mimic the format:
        [====          ]  25% Estimated 30 sec remaining.....
        '''
        # The actual progress bar
        self.current = (self.events * self.size) / self.total
        bar = "  [" + "=" * self.current + " " * (self.size - self.current) + "]"
        
        # The percentage completion display
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
        
