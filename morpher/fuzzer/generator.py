'''
Contains the L{Generator} class for building collections of fuzzed values

@author: Rob Waaser
@contact: robwaaser@gmail.com
@organization: Carnegie Mellon University
@since: October 30, 2011
'''

import random
import struct
import logging

class Generator(object):
    '''
    Used to generate lists of values created by mutating a given value,
    using lists of heuristic values based on type, and values chosen
    at random.
    
    This class operates by accepting a L{struct} style format character
    and an original value. A map is used to match the format string type
    to the appropriate generator functin - for example, unsigned integer
    types of all sizes are fuzzed using the L{_getUints} function. The 
    individual generator functions return the values as a set, ensuring
    that no value is repeated, which is turned into a list and returned
    to the caller. Values are generated according to methods specified
    in the configuration.
    
    @todo: Use memoization to increase performance
    @todo: Examine fuzzing algorithms for possible improvement
    
    @ivar cfg: The L{Config} configuration object for this L{Monitor}
    @ivar log: The L{logging} object for this L{Monitor}
    @ivar mutational: Boolean indicating if mutational values should be used
    @ivar mutaterange: Integer indicating the range of values around the 
                       original value should be produced for mutational 
                       fuzzing
    @ivar heuristic: Boolean indicating if heuristic values should be used
    @ivar random: Boolean indicating if random values should be used
    @ivar randcases: Number of values chosen at random to produce
    @ivar generators: Map of format strings to appropriate generator function
    '''

    def __init__(self, cfg):
        '''
        Store the configuration object, initializes instance variables
        using configuration data, and sets up the generator map.
        
        @param cfg: The configuration object to use
        @type cfg: L{Config} object
        '''
        # The Config object to use
        self.cfg = cfg
        # The logging object to use
        self.log = logging.getLogger(__name__)
        # Boolean indicating mutational method is enabled
        self.mutational = cfg.getboolean('fuzzer', 'mutational')
        # Size of range of values around original to be returned
        self.mutaterange = cfg.getint('fuzzer', 'mutate_range')
        # Boolean indicating heuristic method is enabled
        self.heuristic = cfg.getboolean('fuzzer', 'heuristic')
        # Boolean indicating random method is enabled
        self.random = cfg.getboolean('fuzzer', 'random')
        # Number of random values to return
        self.randcases = cfg.getint('fuzzer', 'random_cases')
        # Each format string type is mapped to a particular
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
    
    def generate(self, fmt, orig):
        '''
        Takes a type and a value and returns a list of fuzzed values,
        which is created using some or all of the methods listed:
        
          1. Mutational: the original value is modified to return 
             values that are similar to the original, such as by 
             adding or subtracting small amounts (for integers)
             
          2. Heuristic: a predetermined list of values is used, where
             the values are chosen based on a high likelihood of 
             creating problems for programs that do not adequately
             check their inputs. For example, if a floating-point
             type is being fuzzed, NaN and Inf values might be used,
             since programs that accepts floats may not correctly
             handle these special and uncommon values.
             
          3. Random: several values are chosen at random from the
             set of legal values for this type.
        
        @param fmt: The format string of the type we are fuzzing
        @type fmt: string
        
        @param orig: The original value of the object we are fuzzing
        @type orig: basic Python value (string, integer, etc)
        
        @return: List of fuzzed values
        @rtype: basic Python value (string, integer, etc) list
        '''
        # Hand off to the appropriate generator function
        return list(self.generators[fmt](fmt, orig))
    
    def _getChars(self, fmt, orig):
        '''
        Generates a fuzzed value list for character types
        
        Mutational values are created by checking if the character is
        a digit or a letter, and using values of the opposite types, 
        as well as lowercase versions of letters if they are given.
        
        Heuristic values used are drawn from a list of path seperators, 
        delimiters, and other characters that often have special meaning,
        as well as unprintable characters and characters outside of the
        legal ASCII values.
        
        @param fmt: The format string of the type we are fuzzing
        @type fmt: string
        
        @param orig: The original value of the character we are fuzzing
        @type orig: single-character string
        
        @return: Set of characters
        @rtype: single-character string set
        '''
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
        '''
        Generates a fuzzed value list for signed integer types.
        
        Mutational values are created by adding and subtracting up
        to (self.mutaterange) from the original value, and multiplying/
        dividing it by the integers 2 and 4 (and their negative 
        counterparts).
        
        Heuristic values are generated by adding and subtracting up
        to 5 from the maximum and minimum legal signed integer values 
        for this type and zero, as well as the max and min values
        divided and multiplied respectively by 2 and 4.
        
        Illegal values (those that can't be expressed by this type) are 
        discarded.
        
        @param fmt: The format string of the type we are fuzzing
        @type fmt: string
        
        @param orig: The original value of the number we are fuzzing
        @type orig: integer
        
        @return: Set of integers
        @rtype: integer set
        '''
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
        '''
        Generates a fuzzed value list for unsigned integer types.
        
        Mutational values are created by adding and subtracting up
        to (self.mutaterange) from the original value, and multiplying/
        dividing it by the integers 2 and 4.
        
        Heuristic values are generated by adding and subtracting up
        to 5 from the maximum and minimum legal unsigned integer values 
        for this type, as well as the max and min values divided and
        multiplied respectively by 2 and 4.
        
        Illegal values (those that can't be expressed by this type) are 
        discarded.
        
        @param fmt: The format string of the type we are fuzzing
        @type fmt: string
        
        @param orig: The original value of the number we are fuzzing
        @type orig: integer
        
        @return: Set of positive integers
        @rtype: integer set
        '''
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
            for x in range(5) :
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
        '''
        Generates fuzzed value list for floating point types.
        
        Mutational values are created by adding and subtracting up
        to (self.mutaterange) from the original value, and multiplying/
        dividing it by the integers 2,3, and 4. Both positive and negative
        versions of these values are added.
        
        Heuristic values are based off the minimum and maximum magnitudes
        expressable as a float, multiplied and divided by 2 through 4, as 
        both positive and negative values. Additional special values that
        are unique to floats are also included (NaN, +0, -0, +Inf, -Inf)
        
        @param fmt: The format string of the type we are fuzzing
        @type fmt: string
        
        @param orig: The original value of the float we are fuzzing
        @type orig: float
         
        @return: Set of floating point values
        @rtype: float set
        '''
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
        '''
        Generates a list of pointers. Mutational fuzzing is
        not performed on pointers since there is a high chance
        that altering a pointer's value will cause it to point
        outside of valid ctypes data and into Python's structures,
        and writing to such an area will likely cause Python to 
        crash even if a C program would not have.
        
        Random values are not used for the same reason.
        
        Heuristic values are just NULL values and a value chosen
        to fall into kernel memory, which will pass checks for
        NULL but cause a segfault upon any read or write.
        
        @param fmt: The format string of the type we are fuzzing
        @type fmt: string
        
        @param orig: The original value of the pointer we are fuzzing
        @type orig: integer
        
        @return: Set of pointer values
        @rtype: integer set
        '''
        values = set()
        # Can't do mutational because pointer will not be to
        # valid memory, it'll point outside valid ctype and crash
        # python - not really a case we want.
        
        # Heuristic values
        if self.heuristic :
            values.add(0)
            values.add(-1)
            values.add(0x80000000)
            
        # Can't do random for the same reason as mutational
        
        return values
    
    