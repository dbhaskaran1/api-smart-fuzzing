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
    # Our Range type, as a tuple of the high and low number
    Range = namedtuple('Range', ['low', 'high'])
    
    def __init__(self, startlist=None):
        '''
        Optional argument allows RangeUnion to be initialized
        from an existing range list
        '''
        # The internal sorted list of non-overlapping ranges
        self.rlist = deque()
        
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
        # Pop ranges from range list, and compare. If ranges overlap, merge
        # and pop the next range; else add the popped range to a 'done' list
        while len(self.rlist) > 0:
            r = self.rlist.popleft()
            # Check for overlap and merge
            if x.low <= r.high + 1 and x.high >= r.low - 1 :
                low = x.low if x.low < r.low else r.low
                high = x.high if x.high > r.high else r.high
                x =  self.Range(low, high)
                continue
            # Check to see if any remaining ranges could possibly overlap
            if x.high < r.low - 1 :
                # Put the current range back before we exit
                self.rlist.appendleft(r)
                break
            left.append(r)
        # Add the merged range to the done list
        left.append(x)
        # Add all of the remaining to the done list
        left.extend(self.rlist)
        # Set range list = done list
        self.rlist = left
                        
            