'''
Created on Oct 30, 2011

@author: Rob
'''
import random
import struct
import logging

class Mutator(object):
    '''
    classdocs
    '''

    def __init__(self, cfg):
        '''
        Constructor
        '''
        self.cfg = cfg
        self.log = logging.getLogger(__name__)
        self.mutational = cfg.getboolean('fuzzer', 'mutational')
        self.mutaterange = cfg.getint('fuzzer', 'mutate_range')
        self.heuristic = cfg.getboolean('fuzzer', 'heuristic')
        self.random = cfg.getboolean('fuzzer', 'random')
        self.randcases = cfg.getint('fuzzer', 'random_cases')
        self.generators = {
                            "c": self._getChars,
                            "b": self._getInts,
                            "B": self._getUints,
                            "h": self._getInts,
                            "H": self._getUints,
                            "i": self._getInts,
                            "I": self._getUints,
                            "l": self._getInts,
                            "L": self._getUints,
                            "q": self._getInts,
                            "Q": self._getUints,
                            "f": self._getFloats,
                            "d": self._getFloats,
                            "P": self._getPointers
                           }
    
    def mutate(self, fmt, orig):
        return self.generators[fmt](fmt, orig)
    
    def _getChars(self, fmt, orig):
        # Get the minimum and maximum possible integer value
        min_val = 0
        max_val = 127
        values = set()
        if self.mutational :
            if orig.isdigit() :
                values.add("a")
                values.add("Z")
            else :
                values.add("0")
                values.add("9")
                values.add(orig.swapcase())
        if self.heuristic :
            values.add("\0") 
            values.add("\r")
            values.add("\n")
            values.add("\b")
            values.add("\t")
            values.add(" ")
            values.add("@")
            values.add("%")
            values.add(":")
            values.add("\\")
            values.add("/")
            values.add("|")
            values.add("=")
            values.add(",")
            values.add(";")
            values.add(")")
            values.add("(")
            values.add("\"")
            values.add(".")
            values.add(chr(255))
        if self.random :
            random.seed()
            for _ in range(0, self.randcases) :
                values.add(chr(random.randint(min_val, max_val)))
        return values
    
    def _getInts(self, fmt, orig):
        # Get the minimum and maximum possible integer value
        min_int = -(2**(struct.calcsize(fmt)*8 - 1))
        max_int = (2**(struct.calcsize(fmt)*8 - 1)) -1
        values = set()
        if self.mutational :
            mut = set()
            # Fuzz in a range around original
            for x in range(self.mutaterange,0, -1):
                mut.add(orig + x)
                mut.add(orig - x)
            # Try negative and positive scaling of value
            mut.add(-orig)
            for e in [orig/2, orig/4, orig*2, orig*4] : 
                mut.add(e)
                mut.add(-e)
            # Might have generated a few illegal values, check for them
            for item in mut:
                if item <= max_int and item >= min_int:
                    values.add(item)
        if self.heuristic :
            for x in range(5) :
                values.add(min_int + x)
                values.add(max_int - x)
                values.add(min_int/2 + x)
                values.add(min_int/2 - x)
                values.add(max_int/2 + x)
                values.add(max_int/2 - x)
                values.add(min_int/4 + x)
                values.add(min_int/4 - x)
                values.add(max_int/4 + x)
                values.add(max_int/4 - x)
                values.add(0 + x)
                values.add(0 - x)
        if self.random :
            random.seed()
            for _ in range(0, self.randcases) :
                values.add(random.randint(min_int, max_int))
        return values
    
    def _getUints(self, fmt, orig):
        # Get the minimum and maximum possible integer value
        min_int = 0
        max_int = (2**(struct.calcsize(fmt)*8)) -1
        values = set()
        if self.mutational :
            mut = set()
            # Fuzz in a range around original
            for x in range(self.mutaterange,0, -1):
                mut.add(orig + x)
                mut.add(orig - x)
            # Try scaling of value
            for e in [orig/2, orig/4, orig*2, orig*4] : 
                mut.add(e)
            # Might have generated a few illegal values, check for them
            for item in mut:
                if item <= max_int and item >= min_int:
                    values.add(item)
        if self.heuristic :
            for x in range(4) :
                values.add(min_int + x)
                values.add(max_int - x)
                values.add(max_int/2 + x)
                values.add(max_int/2 - x)
                values.add(max_int/4 + x)
                values.add(max_int/4 - x)
        if self.random :
            random.seed()
            for _ in range(0, self.randcases) :
                values.add(random.randint(min_int, max_int))
        return values
    
    def _getFloats(self, fmt, orig):
        # Get the rough minimum and maximum positive float values
        if struct.calcsize(fmt) == 8:
            # IEEE double values
            min_float = 10e-323
            max_float = 10e308
        else :
            # IEEE single values
            min_float = 10e-44
            max_float = 10e38
        values = set()
        if self.mutational :
            mut = set()
            # Fuzz in a range around original
            for x in range(self.mutaterange,0, -1):
                mut.add(orig + x)
                mut.add(orig - x)
            # Try scaling of value
            for e in [orig/2, orig/3, orig/4, orig*2, orig*3, orig*4] : 
                mut.add(e)
                mut.add(-e)
            # Might have generated a few illegal values, check for them
            for item in mut:
                if item <= max_float and item >= min_float:
                    values.add(item)
        if self.heuristic :
            values.add(float('nan'))
            values.add(float('inf'))
            values.add(float('-inf'))
            values.add(-0.0)
            values.add(0.0)
            values.add(max_float)
            values.add(min_float)
            values.add(max_float/2)
            values.add(max_float/3)
            values.add(max_float/4)
            values.add(min_float*2)
            values.add(min_float*3)
            values.add(min_float*4)
            values.add(-min_float)
            values.add(-max_float)
            values.add(-min_float*2)
            values.add(-min_float*3)
            values.add(-min_float*4)
            values.add(-max_float/2)
            values.add(-max_float/3)
            values.add(-max_float/4)     
        if self.random :
            random.seed()
            for _ in range(0, self.randcases) :
                sign = random.choice([-1,1])
                values.add(random.random() * 3.4e38 * sign)
        return values
    
    def _getPointers(self, fmt, orig):
        maxp = (2**(struct.calcsize(fmt)*8))- 1
        values = set()
        # Can't do mutational because pointer will not be to
        # valid memory, it'll point outside valid ctype and crash
        # python - not really a case we want.
        if self.heuristic :
            values.add(0)
            values.add(-1)
            values.add(0x80000000)
        if self.random :
            random.seed()
            for _ in range(0, self.randcases) :
                values.add(random.randint(0, maxp))
        return values
    
    