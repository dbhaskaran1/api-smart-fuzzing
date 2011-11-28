'''
Contains the modules used for Morpher's data collection phase.

G{packagetree}

The overall purpose of these modules is to run a series of programs
which use functions exported by a target DLL, hook those functions
and take a "snapshot" of relevant parts of the stack at the moment
of the function call, recording the data so the function call can
be replayed later in its entirety.

L{RangeUnion} is a utility class that implements a data structure
for managing ranges - the idea is that after adding a large number
of potentially overlapping ranges to the L{RangeUnion}, it will
return a minimal set of ranges that has the same coverage as the 
ranges it was given, no more or less, and with no overlapping members.
This is used to make sure that no part of memory is copied twice
when taking a L{Snapshot}. The L{SnapshotManager} is a class that 
uses the L{RangeUnion} to make sure the L{Snapshot} it creates doesn't 
copy more memory than necessary, and carries out the copying of memory
at the moment the L{Snapshot} is created. L{FuncRecorder} is responsible
for actually walking through the stack of a function call and identifying
areas that need to be recorded, while L{TraceRecorder} is responsible
for setting up the program and hooking the function calls to be recorded.
The whole process is coordinated by the top-level L{Collector} object and
is highly dependent on the information output in model.xml by the parser.

@author: Rob Waaser
@contact: robwaaser@gmail.com
@organization: Carnegie Mellon University
@since: October 22, 2011
'''

__all__ = \
[
    "collector",
    "range_union",
    "snapshot_manager",
    "trace_recorder",
    "func_recorder"
]
