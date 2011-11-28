'''
Contains the L{RangeUnion} class for maintaining a "covering" set of ranges

@author: Rob Waaser
@contact: robwaaser@gmail.com
@organization: Carnegie Mellon University
@since: October 26, 2011
'''

from collections import namedtuple
from collections import deque

class RangeUnion(object):
    '''
    Used to maintain a list of ranges 
    
    The class is designed to solve the problem where a list of ranges
    is given and needs to be "simplified" to an equivalent list with 
    the minimum possible number of ranges and no overlaps. The range list
    is maintained as the instance variable rlist, and rlist is updated
    each time a new range is added with the L{add} method.
    
    Ranges are represented by the "Range" L{namedtuple}
    
    @invariant: Intervals in the range list do not overlap, are in sorted
                order from lowest address to highest, and for any two 
                consecutive ranges in the list there is a separation of 
                at least 1 between the ending address of the first and 
                the beginning address of the second.
    
    @todo: Improve performance of the RangeUnion - use a tree structure?
    
    @ivar rlist: A list of Range objects
    '''
    # Our Range type, a tuple of the high and low number
    Range = namedtuple('Range', ['low', 'high'])
    
    def __init__(self, startlist=None):
        '''
        Takes an optional argument that allows this L{RangeUnion} to 
        be initialized from an existing range list, otherwise empty.
        
        @param startlist: The list of ranges to be initialized from
        @type startlist: Range object list
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
        
        @param c: Range to add
        @type c: Range object
        '''
        if len(self.rlist) == 0 :
            c = RangeUnion.Range(c.low, c.high)
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
                        
            