'''
Created on Oct 26, 2011

@author: Rob
'''
from collections import namedtuple
from collections import deque

class RangeUnion(object):
    '''
    Used to maintain a list of ranges (intervals) where the list
    maintains the invariant that all intervals are nonoverlapping,
    in sorted order, and maximal (two consecutive ranges that together
    cover a single unbroken sequence of integers will be merged to one)
    '''
    
    # The internal sorted list of non-overlapping ranges
    rlist = deque()
    
    # Our Range type, as a tuple of the high and low number
    Range = namedtuple('Range', ['low', 'high'])
    
    def __init__(self, startlist=None):
        '''
        Optional argument allows RangeUnion to be initialized
        from an existing range list
        '''
        if startlist :
            for x in startlist :
                self.add(x)
        
    def add(self, c):
        '''
        Given a Range c, adds c to the list of ranges, then merges any
        overlapping members so the list retains the equivalent
        range information but remains sorted and non-overlapping.
        Note that the ranges are at integer granularity, so the
        range (1, 4) and range (5, 7) can be merged to range (1, 7)
        '''
        if len(self.rlist) == 0 :
            self.rlist.append(c)
            return
        x = c
        left = deque()
        while len(self.rlist) > 0:
            r = self.rlist.popleft()
            if x.low <= r.high + 1 and x.high >= r.low - 1 :
                low = x.low if x.low < r.low else r.low
                high = x.high if x.high > r.high else r.high
                x =  self.Range(low, high)
                continue
            if x.high < r.low - 1 :
                self.rlist.appendleft(r)
                break
            left.append(r)
        left.append(x)
        left.extend(self.rlist)
        self.rlist = left
                        
            