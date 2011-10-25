'''
Created on Oct 18, 2011

@author: Rob
'''
import morpher.pydbg.pydbg as pydbg
import morpher.pydbg.defines as defines
import struct
    
def sprintf_handler(dbg):
    addr = dbg.context.Esp + 0xC
    count = dbg.read_process_memory(addr, 4)
    count = int(struct.unpack("L",count)[0])
    print "Caught myself a sprintf with a counter of %d!" % count
    return defines.DBG_CONTINUE

if __name__ == '__main__':

    dbg = pydbg.pydbg()
    pid = int(raw_input("Enter PID of process: "))
    dbg.attach(pid)
    print "Running...."
    sprintf_address = dbg.func_resolve("msvcrt.dll", "sprintf")
    dbg.bp_set(sprintf_address, description="sprintf_address", handler=sprintf_handler)
    dbg.run()
    