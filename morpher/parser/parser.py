'''
Created on Oct 21, 2011

@author: Rob
'''
import xml.dom.minidom as xml

class parser(object):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        
    def parse(self):
        "This is a doc string"
        doc = xml.getDOMImplementation().createDocument(None, "dll", None)
        top = doc.documentElement
        
        func = doc.createElement("function")
        
        addr = doc.createElement("address")
        addr_value = doc.createTextNode("10243")
        addr.appendChild(addr_value)
        func.appendChild(addr)
        
        name = doc.createElement("name")
        name_value = doc.createTextNode("add")
        name.appendChild(name_value)
        func.appendChild(name)
        
        top.appendChild(func)
        
        func = doc.createElement("function")
        
        addr = doc.createElement("address")
        addr_value = doc.createTextNode("9999")
        addr.appendChild(addr_value)
        func.appendChild(addr)
        
        name = doc.createElement("name")
        name_value = doc.createTextNode("sub")
        name.appendChild(name_value)
        func.appendChild(name)
        
        top.appendChild(func)
        
        basedir = "C:\\Users\\Rob\\workspace\\ApiFuzzing\\"
        f = open(basedir + "data\\model.xml", mode="w")
        top.writexml(f, addindent="    ", newl="\n")
        
        