'''
Created on Oct 22, 2011

@author: Rob
'''

class Null(object):
    '''
    Class documentation
    '''
    def __init__(self, *args, **kwargs): pass
    def __call__(self, *args, **kwargs): return self
    def __getattribute__(self, name): return self
    def __setattr__(self, name, value): pass
    def __delattr__(self, name): pass