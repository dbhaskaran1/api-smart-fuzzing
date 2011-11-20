'''
Contains the modules used for Morpher's fuzzing phase.

The overall purpose of these modules is to take the L{Trace} files generated
by the collection phase, modify the recorded values in the traces according to
their types, then replay those function calls in a new process and monitor the
process for signs of hangs or crashes. If a failure is detected, the 
appropriate crash information is stored along with the modifed trace so it 
can be reproduced as needed. 

@author: Rob Waaser
@contact: robwaaser@gmail.com
@organization: Carnegie Mellon University
@since: November 13, 2011
'''

__all__ = \
[
    "fuzzer",
    "harness",
    "monitor",
    "generator"
]
