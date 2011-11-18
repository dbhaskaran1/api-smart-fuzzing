'''
Contains various modules that are shared by more than one package
or do not fall neatly into the scope of other packages.

Currently contains L{Config}, a class used to share configuration 
information between all components of a project; L{log_setup}, which
contains a simple method that initializes the project-wide logging
system; L{StatusReporter}, which contains a class for tracking
and displaying progress in the form of a status bar; and 
L{SectionReporter}, which builds off of L{StatusReporter} to
report the progress of a multi-part program.

G{packagetree}

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
