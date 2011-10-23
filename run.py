'''
Created on Oct 21, 2011

@author: Rob
'''

import sys
import api_fuzzer.parser.funcs as funcs
import api_fuzzer.fuzzer.fuzzer as fuzzer
import api_fuzzer.parser.parser as parser
import api_fuzzer.misc.config as config
import api_fuzzer.misc.logger as logger
    
if __name__ == '__main__':
    
    c = config.create()
    logger.setup()
    '''
    fuzz = fuzzer.fuzzer(dll)
    fuzz.start()
    pid = fuzz.pid
    funcs.get_funcs(os.getcwd() + '\\' + dll)
    p = parser.parser()
    p.parse()
    '''
