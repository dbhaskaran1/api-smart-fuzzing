'''
Created on Oct 6, 2011

@author: Rob Waaser
'''
import ctypes
import os



if __name__ == '__main__':
    
    print "Running using cdll.libTestDLL...."
    kernel32 = ctypes.windll.kernel32
    print "Running using LoadLibrary"
    name = "libTestDLL.dll"
    path = os.path.join(os.getcwd(), name)
    handle  = kernel32.LoadLibraryA(path)
    print "Handle %x" % handle
    error = kernel32.GetLastError()
    print "Load returned error: " + str(error)
    address = kernel32.GetProcAddress(handle, "add_num")
    print kernel32.GetLastError()
    print "Address: %x" % address
    if error == 0 :
        print "Freeing library handle"
        kernel32.FreeLibrary(handle)
    '''
    dll = ctypes.cdll #cdll windll oledll
    print dll.libTestDLL.add_num(2, 2)
    # cdll.kernel32[1]
    # hex(windll.kernel32.GetModuleHandleA(None)) 
    #  all Python types except integers, strings, and unicode strings 
    # have to be wrapped in their corresponding ctypes type, 
    print "Running using CDLL(\"libTestDLL\")...."
    args = [2, 2]
    print ctypes.cdll.LoadLibrary("libTestDLL")[1](*args)
    
    print "Running using LoadLibrary"
    name = "libTestDLL.dll"
    path = os.path.join(os.getcwd(), name)
    
    print "Finding library TestDLL"
    print ctypes.util.find_library("libTestDLL.dll")

    print "Resetting DLL search path...."
    # kernel32.SetDllDirectoryA(None)
    
    p = ctypes.create_string_buffer(500)
    print kernel32.GetDllDirectoryA(500, ctypes.byref(p))
    print kernel32.GetLastError()
    print repr(p.raw)
    print kernel32.GetWindowsDirectoryA(ctypes.byref(p), 500)
    print kernel32.GetLastError()
    print repr(p.raw)
    
    print "My current path:    " + os.getcwd()
    print "Trying to load dll: " + path
    path = path
    handle  = kernel32.LoadLibraryA(path)
    print handle
    error = kernel32.GetLastError()
    print "Load returned error: " + str(error)
    address = kernel32.GetProcAddress(handle, "add_num")
    print kernel32.GetLastError()
    print "Address: %x" % address
    if error == 0 :
        print "Freeing library handle"
        kernel32.FreeLibrary(handle)
'''