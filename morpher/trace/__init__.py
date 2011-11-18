'''
Contains various modules used to model and store data captured from
a function call.

The core components of this module build off each other to encapsulate 
chunks of memory captured from another process, along with enough information
about types, address, etc to be able to reconstruct and replay data to 
a function call. One of the major design goals was to make these objects
serializable so they could be stored to a file or sent through a pipe
and properly reconstructed once they were deserialized.

The contents of memory are captured in the form of L{Block}s, which
provide an interface to read and write their contents. Collections of
blocks are managed by L{Memory} objects; one of their main responsibilities
is to preserve pointer relationships, by recording pointers and 
then "patching" them on demand to point to the same objects after 
deserialization.

Type information is captured mainly through the use of L{Tag} objects, which
merely record an address and a format string similar to those used by the
L{struct} module. A L{TypeManager} object can be used to translate these format
types into L{ctypes} objects suitable as function arguments for a DLL function.
One of the most important aspects of these classes is to properly reconstruct 
L{ctypes} struct and union classes from stored information about user-defined
types.

L{Snapshot} puts all the pieces together in order to capture a function call
in it's entirety. It contains a L{Memory} object with the actual data, a 
collection of L{Tag}s giving types for that data, and a L{TypeManager} that
can translate those tags into meaningful classes. L{Snapshot} is responsible
for using all this information to reconstruct L{ctypes} objects respresenting
the original arguments that can be used in a function call, and in such a way
that all pointers point to the same data that they did when originally captured.

Finally, L{Trace} serves as a top-level object that pairs a list of 
L{Snapshot} objects to be replayed in order, along with the L{TypeManager}
object used by all of those L{Snapshot}s.

@author: Rob Waaser
@contact: robwaaser@gmail.com
@organization: Carnegie Mellon University
@since: November 13, 2011
'''
__all__ = \
[
    "block",
    "snapshot",
    "memory",
    "trace",
    "tag",
    "typemanager"
]
