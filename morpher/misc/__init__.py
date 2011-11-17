'''
Contains various modules that are shared by more than one package
or do not fall neatly into the scope of other packages.

Currently contains L{config}, a class used to share configuration 
information between all components of a project; L{log_setup}, which
contains a simple method that initializes the project-wide logging
system; L{status_reporter}, which contains a class for tracking
and displaying progress in the form of a status bar; and 
L{section_parameter}, which builds off of L{status_reporter} to
report the progress of a multi-part program.

@author: Rob Waaser
@contact: robwaaser@gmail.com
@organization: Carnegie Mellon University
@since: October 22, 2011
'''

__all__ = \
[
    "config",
    "log_setup",
    "status_reporter",
    "section_reporter"
]
