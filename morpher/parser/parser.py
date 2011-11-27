'''
Created on Oct 21, 2011

@author: Rob
'''
import xml.dom.minidom as xml
import logging
import os
import dllexp
import sys
import re
from morpher.misc import status_reporter

from subprocess import Popen, PIPE
from morpher.pycparser.c_parser import CParser

CPPPATH = r'../../tools/tcc/tcc.exe' if sys.platform == 'win32' else 'cpp'

class Parser(object):
    '''
    Parser documentation
    '''

    def __init__ (self, cfg):
        '''
        init documentation
        '''
        # The Config object used for configuration info
        self.cfg = cfg
        # The logging object used for reporting
        self.log = logging.getLogger(__name__)
        # The dllexp.exe wrapper object for getting export data
        self.dllexp = dllexp.DllExp(cfg)
        
        self.targetfile = self.cfg.get('parser', 'headerpath')
        
        self.compiler = self.cfg.get('parser', 'precomppath')
        
        self.compilerflags = self.cfg.get('parser', 'compflags')

    def parse_file(self):
        """ Parse a C file using pycparser.
        
            filename:
                Name of the file you want to parse.
            
            use_cpp:
                Set to True if you want to execute the C pre-processor
                on the file prior to parsing it.
            
            cpp_path:
                If use_cpp is True, this is the path to 'cpp' on your
                system. If no path is provided, it attempts to just
                execute 'cpp', so it must be in your PATH.
            
            cpp_args:
                If use_cpp is True, set this to the command line 
                arguments strings to cpp. Be careful with quotes - 
                it's best to pass a raw string (r'') here. 
                For example:
                r'-I../utils/fake_libc_include'
                If several arguments are required, pass a list of 
                strings.
            
            When successful, an AST is returned. ParseError can be 
            thrown if the file doesn't parse successfully.
            
            Errors from cpp will be printed out. 
        """
        #if use_cpp:   
        path_list = [self.compiler]
        if isinstance(self.compilerflags, list):
            path_list += self.compilerflags
        elif self.compilerflags != '': 
            path_list += [self.compilerflags]
        path_list += [self.targetfile]
           
        pipe = Popen(path_list, stdout=PIPE, universal_newlines=True)
        text = pipe.communicate()[0]
            
#        f = open('foo.txt', 'w')
#        f.write(text)
#        f.close()
        
        # Make the output pycparser compatible
        text = re.sub('__stdcall',"",text)
        text = re.sub('__attribute__\(\(.*?\)\)*',"",text)
        text = re.sub('#.*',"",text)
        
        parser = CParser(lex_optimize=False, yacc_debug=False, yacc_optimize=False)
    
        return parser.parse(text, self.targetfile)

    def parseXML(self, ast, element, name, state, printflag):
        """ 
            Fill in data!!
        """
    
        funcName = ast.__class__.__name__
    
        if funcName == "Decl":
            # Declaration of an object - get the name and pass it on!
            for c in ast.children():                                
                val = self.parseXML(c, element, getattr(ast, ast.attr_names[0]), state, printflag)            
                return val
        elif funcName == "FuncDecl":
            # Function Declaration - Take input from the Decl node for the name, and explore all sub-nodes
            func = self.doc.createElement("function")
            func.setAttribute("name", name)
            if self.text.find(str(name)) != -1:   
                printflag |= 1
            else:
                printflag |= 0  
                  
            for c in ast.children():    
                val = self.parseXML(c, func, name, state, printflag)
                    
            if state == 1 and printflag == 1 and str(name) not in self.xmlMap:                
                self.top.appendChild(func)
                self.xmlMap[str(name)] = 1
            return None 
        elif funcName == "ParamList":
            # The parameter list! List all the parameters!!
            for c in ast.children():
                param = self.doc.createElement("param")
                val = self.parseXML(c, param, name, state, printflag)
                if val != None:
                    param.setAttribute("type", val)
                if state == 1:
                    element.appendChild(param) 
        elif funcName == "PtrDecl":
            for c in ast.children():
                val = self.parseXML(c, element, name, state, printflag)
                if val != None:
                    return "P" + val
        elif funcName == "TypeDecl":
            for c in ast.children():
                val = self.parseXML(c, element, name, state, printflag)
                if val != None:
                    return val
        elif funcName == "Typename":
            for c in ast.children():
                val = self.parseXML(c, element, name, state, printflag)
                if val != None:
                    return val
        elif funcName == "IdentifierType":
            val = getattr(ast, ast.attr_names[0])
            if len(val) > 1:
                if val[0] == "char" and val[1] == "unsigned":
                    return "B"
                elif val[0] == "short" and val[1] == "unsigned":
                    return "H"
                elif val[0] == "int" and val[1] == "unsigned":
                    return "I"
                elif val[0] == "long" and (val[1] == "unsigned"):
                    return "L"
                elif val[0] == "char" and val[1] == "signed":
                    return "c"
                elif val[0] == "short" and val[1] == "signed":
                    return "h"
                elif val[0] == "int" and val[1] == "signed":
                    return "i"
                elif val[0] == "long" and (val[1] == "signed"):
                    return "l"
                else:
                    return ""
            else:
                if val[0] == "char":
                    return "c"
                elif val[0] == "short":
                    return "h"
                elif val[0] == "int":
                    return "i"
                elif val[0] == "long":
                    return "l"
                elif val[0] == "double":
                    return "d"
                elif val[0] == "float":
                    return "f"
                elif val[0] in self.typeMap:
                    iterMap = self.typeMap[val[0]]
                    while len(iterMap) > 2 and iterMap[0:2] == "//":
                        if iterMap[2:] in self.typeMap:
                            iterMap = self.typeMap[str(iterMap[2:])]
                        else:
                            return ""
    
                    return str(iterMap)
                else:
                    return ""
        elif funcName == "Typedef":
            #type = doc.createElement("usertype")
            #type.setAttribute("name", getattr(ast, ast.attr_names[0]))
            #type.setAttribute("id", str(1))
            #type.setAttribute("type", "typedef")
            for c in ast.children():
                val = self.parseXML(c, element, name, state, printflag)
                if val != None:
                    #param = doc.createElement("param")
                    #param.setAttribute("type", val)
                    #type.appendChild(param)
                    self.typeMap[getattr(ast, ast.attr_names[0])] = val
            #element.appendChild(type)
            return None 
        elif funcName == "Struct":
            if getattr(ast, ast.attr_names[0]) not in self.typeMap:
                ind = self.typeMap['#!@#index']
                self.typeMap['#!@#index'] = self.typeMap['#!@#index'] + 1
                self.typeMap[getattr(ast, ast.attr_names[0])] = str(ind)
            else:
                ind = self.typeMap[getattr(ast, ast.attr_names[0])]
                if state != 1:
                    return str(self.typeMap[getattr(ast, ast.attr_names[0])])
                
            changed = 0
    
            typex = self.doc.createElement("usertype")
            #typex.setAttribute("name", getattr(ast, ast.attr_names[0]))
            typex.setAttribute("id", str(ind))
            typex.setAttribute("type", "struct")
            
            if self.text.find(str(getattr(ast, ast.attr_names[0]))) != -1:   
                printflag |= 1
            else:
                printflag |= 0
                  
            for c in ast.children():
                val = self.parseXML(c, typex, name, state, printflag)
                if val != None:
                    param = self.doc.createElement("param")
                    param.setAttribute("type", val)
                    typex.appendChild(param)
                    changed = 1
            if changed == 1:
                if state == 1 and printflag == 1 and str(getattr(ast, ast.attr_names[0])) not in self.xmlMap:
                    self.top.appendChild(typex)
                    self.xmlMap[str(getattr(ast, ast.attr_names[0]))] = 1
                return str(ind)
            else:
                #if getattr(ast, ast.attr_names[0]) not in self.typeMap:
                #    self.typeMap['#!@#index'] = self.typeMap['#!@#index'] - 1
                #return "//"+getattr(ast, ast.attr_names[0])
                return str(ind)
            #else:
            #   return str(typeMap[getattr(ast, ast.attr_names[0])])
        elif funcName == "Union":
            if getattr(ast, ast.attr_names[0]) not in self.typeMap:
                ind = self.typeMap['#!@#index']
                self.typeMap['#!@#index'] = self.typeMap['#!@#index'] + 1
            else:
                ind = self.typeMap[getattr(ast, ast.attr_names[0])]
                
            changed = 0
    
            typex = self.doc.createElement("usertype")
            #type.setAttribute("name", getattr(ast, ast.attr_names[0]))
            typex.setAttribute("id", str(ind))
            typex.setAttribute("type", "union")
            
            if self.text.find(str(getattr(ast, ast.attr_names[0]))) != -1:   
                printflag |= 1
            else:
                printflag |= 0             
            
            for c in ast.children():
                val = self.parseXML(c, typex, name, state, printflag)
                if val != None:
                    param = self.doc.createElement("param")
                    param.setAttribute("type", val)
                    typex.appendChild(param)
                    self.typeMap[getattr(ast, ast.attr_names[0])] = str(ind)
                    changed = 1
            if changed == 1:
                if state == 1 and printflag == 1 and str(getattr(ast, ast.attr_names[0])) not in self.xmlMap:
                    self.top.appendChild(typex)
                    self.xmlMap[str(getattr(ast, ast.attr_names[0]))] = 1
                return str(ind)
            else:
                #if getattr(ast, ast.attr_names[0]) not in self.typeMap:
                #    self.typeMap['#!@#index'] = self.typeMap['#!@#index'] - 1
                #return "//"+getattr(ast, ast.attr_names[0])
                return str(ind)
            #else:
            #    return str(typeMap[name])
        elif funcName == "Enum":
            return "i"
        elif funcName == "Constant":
            for c in ast.children():
                val = self.parseXML(c, element, None, state, printflag)
            return "["+getattr(ast, ast.attr_names[1])+"]"
        elif funcName == "ArrayDecl":
            val = ""
            for c in ast.children():
                getVal = self.parseXML(c, element, None, state, printflag)
                if getVal != None:
                    val += getVal
            return val
        else:
            val = ""
            for c in ast.children():
                val = self.parseXML(c, element, None, state, printflag)
            return val

    def parse(self):
        '''
        Analyzes the target DLL and header file to retrieve function prototypes.
        Outputs a XML file containing a model of the exported prototypes
        '''
        # Get relevant configuration information
        datadir = self.cfg.get('directories', 'data')
        modelpath = os.path.join(datadir, 'model.xml')
        
        # Check if parsing is enabled
        if not self.cfg.getboolean('parser', 'enabled') : 
            self.log.info("Parsing is disabled")
            print "  Parser DISABLED\n"
            return
            
        sr = status_reporter.StatusReporter(total=5)
        sr.start("  Parser is running...")
        # Parsing is enabled
        self.log.info("Beginning parse routine")
        
        # Retrieve the export table from the DLL
        #exportlist = self.dllexp.getFunctions()
        sr.pulse()
        
        ast = self.parse_file()
        sr.pulse()
        self.text = str(open(self.targetfile, 'rU').read())
    
        # Create the XML tree    
        self.log.info("Creating the XML model")
        self.doc = xml.getDOMImplementation().createDocument(None, "dll", None)
        self.top = self.doc.documentElement
        
        self.typeMap = {}
        self.typeMap['#!@#index'] = 1
        
        self.xmlMap = {}
    
        self.parseXML(ast, self.top, None, 0, 0)
        sr.pulse()
        self.parseXML(ast, self.top, None, 1, 0)
        sr.pulse()
        # Add function nodes
        #for (fname, ordinal, addr) in exportlist :
        #    func = doc.createElement("function")
        #    func.setAttribute("name", fname)
        #    func.setAttribute("ordinal", str(ordinal))
        #    func.setAttribute("address", str(addr))
        #    top.appendChild(func)
            
        # Write out the model file
        self.log.info("Writing XML tree to model file")
        if self.log.isEnabledFor(logging.DEBUG) :
            xmlstr = self.top.toprettyxml(indent="    ", newl="\n")
            self.log.debug("\n\nXML Tree:\n%s\n", xmlstr)
        try :
            f = open(modelpath, mode="w")
        except :
            msg = "Couldn't open %s"
            self.log.exception(msg, modelpath)
            raise Exception(msg % modelpath)
        self.top.writexml(f, addindent="    ", newl="\n")
        f.close()
        sr.pulse()