'''
Created on Oct 21, 2011

@author: Rob
'''

import sys
import morpher.parser.funcs as funcs
import morpher.fuzzer.fuzzer as fuzzer
import morpher.parser.parser as parser
import morpher.misc.config as config
import morpher.misc.logger as logger
    
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