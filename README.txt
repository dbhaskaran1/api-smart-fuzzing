Morpher
Version 0.1
October 21, 2011

Authors:
Robert Waaser (rwaaser)
Erik Schmidt (emschmid)
Piyush Sharma (piyushs)

Installation:

Windows only
Requires 32 bit Python (tested with 2.7)
Tested for 32-bit Windows DLLs

Structure:

Root - top level directory
-morpher - main python package
--morpher.py - top-level module
--fuzzer - module for running fuzz tests
--collector - module for recording API calls and data
--parser - module for determining function prototypes
--pydbg - debugger module pulled from Pai Mei framework
--utils - Pai Mei utilities, mainly hooking and crash binning
--misc - shared or miscellaneous modules
-data - files generated by Morpher
--crashers - stores data on crashes detected during fuzzing
--recordings - holds data collected by the collection script
-logs - holds log files generated by Morpher
-tools - holds external tools run by Morpher
-run.py - entry point for tool, front-end for morpher.py
-config.ini - configuration information
-README.txt - this document

