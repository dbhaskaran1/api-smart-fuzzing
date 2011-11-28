'''
Contains the modules used for the Morpher API-fuzzing utility

G{packagetree}

Morpher is a API fuzzing tool for Windows Dynamically Linked Libraries (DLLs).
Morpher's methods are based around two major ideas:

  1. Mutational fuzzing - Many fuzzers either
     generate valid data for the API calls, which requires the fuzzer to
     understand the API and how it is used, or generate completely random
     data for API calls, which is often invalid and does not exercise
     any of the DLL's code beyond preliminary input sanitization.
     Morpher takes a different route by running programs supplied by the 
     user that use the DLL functions and "capturing" these function
     calls as they occur. The arguments to these function calls are
     then fuzzed individually and the function calls are replayed to
     the DLL. This method of "mutating" known valid calls is able to
     generate invalid calls that are more likely to pass input checking
     without requiring any knowledge of the API beforehand.
     
  2. Understanding argument types - Some function parameters are more complex
     than others - for example, an argument might include a pointer to a 
     structure in memory, which may contain more pointers, etc. If we don't 
     acknowledge these relationships we may fail to fuzz values passed to
     the function that aren't the actual arguments. In addition, knowing
     the types associated with the data allows us to fuzz it intelligently - 
     for example if we know a value is an integer, we can fuzz it
     mutationally by negating the value, or heuristically by replacing it
     with the maximum representable positive value.
     
Morpher accepts a target DLL, the header files for the DLL, and a list of
programs that use the DLL. It parses the header files to create a model
of the DLL's function prototypes, runs the given programs and records their
function calls, then fuzzes and replays those function calls to the DLL
and monitors the function call for signs of a crash or hang. Crashes and
hangs are recorded with enough information that they can be inspected in
detail by a reverse engineer to determine the cause of the problem.

Morpher is designed as a black-box package, so a Morpher object can be 
instantiated and used in an application, or the whole tool can be used
from the command line by a minimal script wrapper. Most of Morpher's
functionality is controlled by a central Config object, which is controlled
in turn by the data in a configuration INI file.

@author: Rob Waaser
@contact: robwaaser@gmail.com
@organization: Carnegie Mellon University
@since: October 21, 2011
'''

__all__ = \
[
    "morpher",
    "collector",
    "fuzzer",
    "misc",
    "parser",
    "pydbg",
    "utils",
    "trace",
    "ply",
    "pycparser"
]
