'''
Created on Oct 6, 2011

@author: Rob
'''
import socket
import time
import os
from ctypes import cdll, c_char_p

if __name__ == '__main__':
    print "My pid: %d" % os.getpid()
    x = socket.getfqdn()
    print "Current host: " + x
    msvcrt = cdll.msvcrt
    counter = 0
    while True:
        s = c_char_p("A"*50)
        msvcrt.sprintf(s, "Counter: %d", counter)
        print s.value
        time.sleep(2)
        counter += 1
    