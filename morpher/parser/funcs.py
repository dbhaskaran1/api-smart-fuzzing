'''
Created on Oct 22, 2011

@author: Rob
'''
import subprocess
import csv

def get_funcs(dllpath):
    base = 'C:\\Users\\Rob\\workspace\\ApiFuzzing\\'
    #os.getcwd()
    outname = 'functions.csv'
    toolname = 'dllexp.exe'
    output = base + 'data\\' + outname
    tool = base + 'tools\\' + toolname
    args = [tool, '/from_files', dllpath, '/scomma', output]
    ret = subprocess.call(args)
    f = open(output)
    result = csv.DictReader(f, ['name','addr_abs', 'addr_rel', 'ordinal', 'dll', 'path', 'type'])
    print "Discovered exported functions of %s" % dllpath
    for r in result :
        print "%(name)s" % r
    return ret