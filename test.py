'''
Created on Oct 26, 2011

@author: Rob
'''
from morpher.misc import block, memory, config, statusreporter, sectionreporter, typeconvert
from morpher.fuzzer import harness, monitor, fuzzer, mutator
from morpher.trace import typemanager, trace, snapshot, tag
import ctypes
import pickle
import os
import time
import run
import sys
import struct
import xml.dom.minidom as xml

def printm(m):
    print "Ordinal %d" % m.ordinal
    print m.read(0x1000, fmt="8s")
    print m.read(0x2000, fmt="PP")
    print m.read(0x3000, fmt="PI")
    print m.read(0x4000, fmt="2sP2s")
    
def testmem():
    
    lst = []
    b = block.Block(0x1000, "\x41\x42\x43\x44\x45\x46\x47\x48")
    lst.append(b)
    b = block.Block(0x2000, "\x00\x10\x00\x00\x00\x30\x00\x00")
    lst.append(b)
    b = block.Block(0x3000, "\x00\x10\x00\x00\x05\x00\x00\x00")
    lst.append(b)
    b = block.Block(0x4000, "\x41\x42\x00\x00\x04\x30\x00\x00\x43\x44")
    lst.append(b)
    
    m = memory.Memory(0, lst)
    m.registerPointer(0x2000)
    m.registerPointer(0x2004)
    m.registerPointer(0x3000)
    m.registerPointer(0x4004)
    
    print "Original:"
    
    printm(m)
    m.setArgs(0x1000, "II")
    print m.getArgs()
    
    print "Patched:"
    m.patch()
    
    printm(m)
    ptr = m.read(0x4004, fmt="P")[0] 
    print ptr
    c = ctypes.c_int.from_address(ptr)
    print c
    
    print "SetArgs:"
    m.setArgs(0x4004, "Icc")
    print m.getArgs()
    
def testopen():
    
    print "After save and load:"
    
    path = os.getcwd()
    path = os.path.join(path, "data", "fuzzed.pkl")
    print path
    f = open(path, "rb")
    fuzz = pickle.load(f)
    f.close()
    for b in fuzz :
        #b.setActive(True)
        print b.read(0x1000, 8)
        print "Ordinal %d ESP %x fmt %s" %(b.ordinal, b.esp, b.arg_fmt)
        print b.mem
        print b.getArgs()
    
    return

    
def testwrite():
    mlst = []
    k = block.Block(0x1000, "\x05\x00\x00\x00\x06\x00\x00\x00")
    mlst.append(k)
    k = block.Block(0x2000, "\x07\x00\x00\x00\x08\x00\x00\x00")
    mlst.append(k)
    
    mk = memory.Memory(0, mlst)
    mk.setArgs(0x1000, "II")
    print mk.getArgs()
    
    mk.registerPointer(0x2000)
    mk.registerPointer(0x2004)
    
    print mk.toString()
    
    path = os.getcwd()
    path = os.path.join(path, "data", "fuzzed.pkl")
    print path
    if os.path.isfile(path) :
        os.remove(path)
        
    f = open(path, "wb")
    print "Ordinal %d ESP %x fmt %s" %(mk.ordinal, mk.esp, mk.arg_fmt)
    print mk.mem
    print "Pickle:"
    lst = [mk]
    for m in lst : 
        print m.read(0x1000, 8)
        
    pickle.dump(lst, f)
    f.close()
    
def testHarness():
    lst = []
    k = block.Block(0x1000, "\x05\x00\x00\x00\x06\x00\x00\x00")
    lst.append(k)
    k = block.Block(0x2000, "\x11\x00\x00\x00\x08\x00\x00\x00")
    lst.append(k)
    
    m = memory.Memory(2, lst)
    m.setArgs(0x2000, "II")

    path = os.getcwd()
    path = os.path.join(path, "data", "fuzzed.pkl")
    f = open(path, "wb")
    pickle.dump(m, f)
    f.close()
    # run the test

    path = os.getcwd()
    path = os.path.join(path, "data", "cfg.pkl")
    cfg = config.Config()
    cfg.setupLogging("morpher")
        # The logging object used for reporting
    log = cfg.getLogger("morpher.morpher")
    log.info(cfg.toString())

    f = open(path,"wb")
    pickle.dump(cfg, f)
    f.close()
    h = harness.Harness(cfg)
    print "IsAlive: " + str(h.is_alive())
    print "Pid: " + str(h.pid)
    
    h.start()
    time.sleep(2)
    print "started harness and slept 2 secs"
    print "IsAlive: " + str(h.is_alive())
    print "Pid: " + str(h.pid)
    
    h.terminate()
    h.join() # Need to do this to collect exit code
    print h.exitcode
    # while True :
    #   pass

def testMonitorHang():
    trace = []
    
    lst = []
    k = block.Block(0x1000, "\x03\x00\x00\x00\x41\x00\x00\x00")
    lst.append(k)
    
    m = memory.Memory(1, lst)
    m.setArgs(0x1000, "Ic")
    trace.append(m)
    
    lst = []
    k = block.Block(0x1000, "\x30\x00\x00\x00\x00\x00\x00\x00")
    lst.append(k)
    k = block.Block(0x2000, "\x30\x00\x00\x00\x00\x00\x00\x00")
    lst.append(k)
    
    m = memory.Memory(1, lst)
    m.setArgs(0x2000, "Ic")
    trace.append(m)
    
    lst = []
    k = block.Block(0x1000, "\x01\x00\x00\x00\x42\x00\x00\x00")
    lst.append(k)
    
    m = memory.Memory(1, lst)
    m.setArgs(0x1000, "Ic")
    trace.append(m)
    
    cfg = config.Config()
    cfg.setupLogging("morpher")
        # The logging object used for reporting
    log = cfg.getLogger("morpher.morpher")
    log.info(cfg.toString())
    print "Calling fuzzer"
    fuzz = monitor.Monitor(cfg, 1)
    fuzz.run(trace)
    print "Exiting"
    
def testMonitorCrash():
    trace = []
    
    lst = []
    k = block.Block(0x1000, "\x00\x00\x00\x00\x05\x00\x00\x00")
    lst.append(k)
    
    m = memory.Memory(2, lst)
    m.setArgs(0x1000, "II")
    trace.append(m)
    
    lst = []
    k = block.Block(0x1000, "\x00\x00\x00\x00\x05\x00\x00\x00")
    lst.append(k)
    k = block.Block(0x2000, "\x11\x00\x00\x00\x08\x00\x00\x00")
    lst.append(k)
    
    m = memory.Memory(2, lst)
    m.setArgs(0x1000, "II")
    trace.append(m)
    
    cfg = config.Config()
    cfg.setupLogging("morpher")
        # The logging object used for reporting
    log = cfg.getLogger("morpher.morpher")
    log.info(cfg.toString())
    print "Calling fuzzer"
    fuzz = monitor.Monitor(cfg)
    fuzz.run(trace)
    
    trace = []
    
    lst = []
    k = block.Block(0x1000, "\x00\x00\x00\x00\x04\x00\x00\x00")
    lst.append(k)
    k = block.Block(0x2000, "\x11\x00\x00\x00\x08\x00\x00\x00")
    lst.append(k)
    
    m = memory.Memory(2, lst)
    m.setArgs(0x1000, "II")
    trace.append(m)
    
    fuzz.setTraceNum(1)
    fuzz.run(trace)
    print "Exiting"
    
def testPatching():
    trace = []
    
    lst = []
    k = block.Block(0x1000, "\x04\x20\x00\x00\x05\x00\x00\x00")
    lst.append(k)
    k = block.Block(0x2000, "\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF")
    lst.append(k)
    
    m = memory.Memory(2, lst)
    m.registerPointer(0x1000)
    m.setArgs(0x1000, "PI")
    trace.append(m)
    
    cfg = config.Config()
    cfg.setupLogging("morpher")
        # The logging object used for reporting
    log = cfg.getLogger("morpher.morpher")
    log.info(cfg.toString())
    print "Calling monitor"
    fuzz = monitor.Monitor(cfg)
    fuzz.run(trace)
    
    print "Exiting"    
    
def testFuzzing():
    cfg = config.Config()
    cfg.setupLogging("morpher")
        # The logging object used for reporting
    log = cfg.getLogger("morpher.morpher")
    log.info(cfg.toString())
    print "Calling Fuzzer"
    fuzz = fuzzer.Fuzzer(cfg)
    fuzz.fuzz()
    
    print "Exiting"  
    
def testMutator():
    cfg = config.Config()
    cfg.setupLogging("morpher")
        # The logging object used for reporting
    log = cfg.getLogger("morpher.morpher")
    log.info(cfg.toString())
    print "Calling Mutator"
    mut = mutator.Mutator(cfg)
    print "Mutating c, A"
    print mut.mutate("c", "A")
    print "Mutating I, 32"
    print mut.mutate("I", 32)
    print "Mutating i, 32"
    print mut.mutate("i", 32)
    print "Mutating h, 32"
    print mut.mutate("h", 32)
    print "Mutating Q, 4000000000000"
    print mut.mutate("Q", 4000000000000)
    print "Mutating f, 3.14"
    print mut.mutate("f", 3.14)
    print "Mutating P, 0xdeadbeef"
    print mut.mutate("P", 0xdeadbeef)
    
    print "Exiting"
    
def testCountValues():
    cfg = config.Config()
    print "Calling Mutator"
    mut = mutator.Mutator(cfg)
    print "Mutating char"
    print len(mut._getChars("c", "A"))
    print "Mutating int"
    print len(mut._getInts("i", 32))
    print "Mutating unsigned int"
    print len(mut._getUints("i", 32))
    print "Mutating floats"
    print len(mut._getFloats("f", 32))
    print "Mutating pointers"
    print len(mut._getPointers("P", 32))

    
def testPlayback(filename):
    run.playback(filename)
    
def testProgressBar():
    # works for windows
    # Twenty ='s seems best
    sys.stdout.write("[=    ]\r")
    time.sleep(1)
    sys.stdout.write("[==   ]\r")
    time.sleep(1)
    sys.stdout.write("[===  ]\r")
    time.sleep(1)
    sys.stdout.write("[==== ]\r")
    time.sleep(1)
    sys.stdout.write("[=====] Done!\n")

    #if sys.platform.lower().startswith('win'):
    #           print self, '\r',
    #       else:
    #           print self, chr(27) + '[A'
    
def testStatusReporter():
    sr = statusreporter.StatusReporter(total=30)
    i = 0
    sr.start("Running StatusReporter test...")
    while i < 30 :
        time.sleep(1)
        sr.pulse()
        i += 1

def testSectionReporter():
    sr = sectionreporter.SectionReporter(3)
    i = 0
    sr.start("Running SectionReporter test...")
    sr.startSection(1, 10)
    while i < 10 :
        time.sleep(1)
        sr.pulse()
        i += 1
    sr.endSection()
    sr.startSection(2, 5)
    i = 0
    while i < 5 :
        time.sleep(2)
        sr.pulse()
        i += 1
    sr.endSection()
    sr.startSection(3, 20)
    i = 0
    while i < 10 :
        time.sleep(1)
        sr.pulse(2)
        i += 1
    sr.endSection()
    print "Done with test"
    
def testTypes():
    modelpath = "data\\model.xml"
    f = open(modelpath)
    model = xml.parse(f).getElementsByTagName("dll")[0]
    f.close()
    tc = typemanager.TypeManager(model)
    # Write it to a pickle file
    path = "junk\\test.pkl"
    f = open(path, "wb")
    pickle.dump(tc, f)
    f.close()
    
    # Read it back in
    path = "junk\\test.pkl"
    f = open(path, "rb")
    newtc = pickle.load(f)
    f.close()
    
    myclass = newtc.getClass("2")
    print ctypes.alignment(myclass)
    print ctypes.sizeof(myclass)
    print myclass._fields_
    myinst = myclass('A', 0x7, 0x0, 'B')
    print getattr(myinst, "field-0")

def testSnapshot():
    modelpath = "data\\model.xml"
    f = open(modelpath)
    model = xml.parse(f).getElementsByTagName("dll")[0]
    f.close()

    
    lst = []
    k = block.Block(0x1000, "\x41\x00\x07\x00\xFF\xFF\xFF\xFF" + "\x00\x00\x00\x00\x00\x00\x00\x00" + "\x42\xFF\xFF\xFF\xFF\xFF\xFF\xFF" + "\x00\x00\x00\x00\x00\x00\x00\x00")
    lst.append(k)
    k = block.Block(0x2000, "\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF")
    lst.append(k)
    
    s = snapshot.Snapshot(2, lst)
    argtag = tag.Tag(0x1000, "4")
    s.addTag(argtag)
    args = [argtag]
    s.setArgs(args)
    
    mytrace = trace.Trace(model, [s])
    
    # Write it to a pickle file
    path = "junk\\test.pkl"
    f = open(path, "wb")
    pickle.dump(mytrace, f)
    f.close()
    
    # Read it back in
    path = "junk\\test.pkl"
    f = open(path, "rb")
    mytrace = pickle.load(f)
    f.close()
    
    for args in mytrace.replay() :
        print args[0]
        print args[0].field_0
        print args[0].field_0.field_0
        print args[0].field_0.field_1
        print args[0].field_0.field_2
        print args[0].field_0.field_3
        print args[0].field_1
        print args[0].field_1.field_0
        print args[0].field_1.field_1
        print args[0].field_1.field_2

if __name__ == '__main__':
    testSnapshot()
    
        
    
    '''
    b = block.Block(0xbfff, "\x41\x42\x43\x00\x07\x00\x00\x00")
    print b.contains(0xbfff, 4)
    print b.contains(0xbffe, 9)
    print b.read(0xbfff, 4)
    print b.read(0xc001, 2)
    print b.read(0xc003, fmt="2H")
    b.write(0xbfff,  ("\x43","\x45"), fmt="2c")
    print b.read(0xbfff, 4)
    b.write(0xbfff, "\x44\x44")
    print b.read(0xc003, fmt="L")
    b.write(0xbfff, "\x44\x44")
    print b.read(0xbfff, 4)
    b.write(0xc000, ("EE",), fmt="2s")
    print b.read(0xbfff, 4)
    
    try:
        print ctypes.memmove(b.translate(0xbfff), 0x00000000, 8)
    except :
        print "Oh no! Access violation"
    print "I'm fine though"
    '''