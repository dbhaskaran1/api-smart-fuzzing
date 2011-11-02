'''
Created on Nov 2, 2011

@author: Rob
'''
import statusreporter

class SectionReporter(object):
    '''
    classdocs
    '''


    def __init__(self, numsections):
        '''
        Constructor
        '''
        # A 100-event status bar
        self.reporter = statusreporter.StatusReporter()
        self.numsections = numsections
        self.cursection = None
        self.cursectiontotal = None
        self.curevents = None
        
    def start(self, msg="Status:"):
        self.reporter.start(msg=msg)
        
    def startSection(self, section, numevents):
        self.cursection = section
        self.curtotal = numevents
        self.curevents = (self.cursection - 1)*numevents
        
    def pulse(self, events=1):
        self.curevents += events
        percent = (self.curevents*100)/(self.numsections*self.curtotal)
        if percent >= 100 : 
            percent = 99
        maxpercent = (self.cursection*100)/self.numsections
        if percent >= maxpercent :
            percent = maxpercent
        self.reporter.correct(percent)
        
    def endSection(self):
        if self.cursection == self.numsections :
            self.reporter.done()
        else :
            percent = (self.cursection*100)/self.numsections
            self.reporter.correct(percent)