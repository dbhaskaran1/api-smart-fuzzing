'''
Created on Oct 26, 2011

@author: Rob
'''
import ctypes

fmt2ctype = {
             "c": ctypes.c_char,
             "b": ctypes.c_byte,
             "B": ctypes.c_ubyte,
             "h": ctypes.c_short,
             "H": ctypes.c_ushort,
             "i": ctypes.c_int,
             "I": ctypes.c_uint,
             "l": ctypes.c_long,
             "L": ctypes.c_ulong,
             "q": ctypes.c_longlong,
             "Q": ctypes.c_ulonglong,
             "f": ctypes.c_float,
             "d": ctypes.c_double,
             "P": ctypes.c_void_p
            }

