'''
Created on Oct 21, 2011

@author: Erik Schmidt
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
        
        # split header files separated by ';'
        tmp = self.cfg.get('parser', 'headerpath')
        self.targetfile = tmp.split(';')
        
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
  
        path_list = [self.compiler]
        if isinstance(self.compilerflags, list):
            path_list += self.compilerflags
        elif self.compilerflags != '': 
            path_list += [self.compilerflags]
        path_list += self.targetfile
           
        self.log.info("Retrieve the preprocessed code from TCC")
        pipe = Popen(path_list, stdout=PIPE, universal_newlines=True)
        text = pipe.communicate()[0]
        
        # Make the output pycparser compatible
        text = re.sub('__stdcall',"",text)
        text = re.sub('__attribute__\(\(.*?\)\)*',"",text)
        #text = re.sub('#.*',"",text)
        #text = re.sub('extern \"C\"', "", text)
        
        self.log.info("Parsing the preprocessed code using pycparser")
        parser = CParser(lex_optimize=False, yacc_debug=False, yacc_optimize=False)
    
        return parser.parse(text, self.targetfile)

    def parseXML(self, ast, element, name, printflag):
        """ 
            Fill in data!!
        """
    
        funcName = ast.__class__.__name__
    
        if funcName == "Decl":
            # Declaration of an object - get the name and pass it on!
            for c in ast.children():                                
                val = self.parseXML(c, element, getattr(ast, ast.attr_names[0]), printflag)            
                return val
        elif funcName == "FuncDecl":
            # Function Declaration - Take input from the Decl node for the name, and explore all sub-nodes
            func = self.doc.createElement("function")
            func.setAttribute("name", name)

            if str(name) in self.text:
                printflag |= 1
            else:
                printflag |= 0  
                  
            for c in ast.children():    
                val = self.parseXML(c, func, name, printflag)
                    
            if printflag == 1:                
                self.top.appendChild(func)
                self.numFuncIncluded = self.numFuncIncluded + 1
            return None 
        elif funcName == "ParamList":
            # The parameter list! List all the parameters!!
            for c in ast.children():
                param = self.doc.createElement("param")
                val = self.parseXML(c, param, name, printflag)
                if val != None:
                    if val != "":
                        if val.find("[") != -1:
                            val = val[:val.find("[")]
                        param.setAttribute("type", val)
                        element.appendChild(param) 
        elif funcName == "PtrDecl":
            for c in ast.children():
                val = self.parseXML(c, element, name, printflag)
                if val != None:
                    return "P" + val
        elif funcName == "TypeDecl":
            for c in ast.children():
                val = self.parseXML(c, element, name, printflag)
                if val != None:
                    return val
        elif funcName == "Typename":
            for c in ast.children():
                val = self.parseXML(c, element, name, printflag)
                if val != None:
                    return val
        elif funcName == "IdentifierType":
            val = getattr(ast, ast.attr_names[0])
            if len(val) > 2:
                if val[0] == "unsigned" and val[1] == "long" and val[2] == "long":
                    return "L"
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
                elif val[0] == "long" and val[1] == "long":
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
                    iterPMap = iterMap
                    if iterMap.rfind("P") != -1:
                        iterPMap = iterMap[iterMap.rfind("P")+1:]
                    if iterPMap in self.xmlMap and printflag == 1:
                        c = self.xmlMap[iterPMap]
                        del self.xmlMap[iterPMap]
                        val = self.parseXML(c, None, None, printflag)
                    return str(iterMap)
                else:
                    return ""
        elif funcName == "Typedef":
            for c in ast.children():
                val = self.parseXML(c, element, name, printflag)
                if val != None:
                    self.typeMap[getattr(ast, ast.attr_names[0])] = val
            return None 
        elif funcName == "Struct":
            if getattr(ast, ast.attr_names[0]) in self.typeMap:
                ind = self.typeMap[getattr(ast, ast.attr_names[0])]
            elif getattr(ast, ast.attr_names[0]) != None and "//" + getattr(ast, ast.attr_names[0]) in self.typeMap:
                ind = self.typeMap["//" + getattr(ast, ast.attr_names[0])]
            else:
                ind = self.typeMap['#!@#index']
                self.typeMap['#!@#index'] = self.typeMap['#!@#index'] + 1
                self.typeMap[getattr(ast, ast.attr_names[0])] = str(ind) 
            
            changed = 0
    
            typex = self.doc.createElement("usertype")
            typex.setAttribute("id", str(ind))
            typex.setAttribute("type", "struct")
            
            if str(getattr(ast, ast.attr_names[0])) in self.text:
                printflag |= 1
            else:
                printflag |= 0
                  
            for c in ast.children():
                val = self.parseXML(c, typex, name, printflag)
                if val != None:
                    if val != "":
                        total = 1
                        arrays = val.split("[")
                        if len(arrays) > 1:
                            for i in range(len(arrays) - 1):
                                total *= int(arrays[i+1][:-1])
                            val = arrays[0]
                        for i in range(total):
                            param = self.doc.createElement("param")
                            param.setAttribute("type", val)
                            typex.appendChild(param)
                        changed = 1
            
            if changed == 1 and printflag == 0:
                self.xmlMap[str(ind)] = ast
            if printflag == 1:
                self.top.appendChild(typex)
                
            return str(ind)
        elif funcName == "Union":
            if getattr(ast, ast.attr_names[0]) in self.typeMap:
                ind = self.typeMap[getattr(ast, ast.attr_names[0])]
            elif getattr(ast, ast.attr_names[0]) != None and "//" + getattr(ast, ast.attr_names[0]) in self.typeMap:
                ind = self.typeMap["//" + getattr(ast, ast.attr_names[0])]
            else:
                ind = self.typeMap['#!@#index']
                self.typeMap['#!@#index'] = self.typeMap['#!@#index'] + 1
                self.typeMap[getattr(ast, ast.attr_names[0])] = str(ind) 
                
            changed = 0
    
            typex = self.doc.createElement("usertype")
            typex.setAttribute("id", str(ind))
            typex.setAttribute("type", "union")
            
            if str(getattr(ast, ast.attr_names[0])) in self.text:
                printflag |= 1
            else:
                printflag |= 0             
            
            for c in ast.children():
                val = self.parseXML(c, typex, name, printflag)
                if val != None:
                    if val != "":
                        total = 1
                        arrays = val.split("[")
                        if len(arrays) > 1:
                            for i in range(len(arrays) - 1):
                                total *= int(arrays[i+1][:-1])
                            val = arrays[0]
                        for i in range(total):
                            param = self.doc.createElement("param")
                            param.setAttribute("type", val)
                            typex.appendChild(param)
                        changed = 1
                    
            if changed == 1 and printflag == 0:
                self.xmlMap[str(ind)] = ast
            if printflag == 1:
                self.top.appendChild(typex)
                
            return str(ind)
        elif funcName == "Enum":
            return "i"
        elif funcName == "Constant":
            for c in ast.children():
                val = self.parseXML(c, element, None, printflag)
            return "[" + getattr(ast, ast.attr_names[1]) + "]"
        elif funcName == "ArrayDecl":
            val = ""
            for c in ast.children():
                getVal = self.parseXML(c, element, None, printflag)
                if getVal != None:
                    val += getVal
            return val
        else:
            val = ""
            for c in ast.children():
                val = self.parseXML(c, element, None, printflag)
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
        
        self.numFuncIncluded = 0
        
        self.log.info("Getting DLL Explorer functions")
        # Retrieve the export table from the DLL
        exportlist = self.dllexp.getFunctions()
        sr.pulse()
        
        ast = self.parse_file()
        sr.pulse()
    
        # Create the XML tree    
        self.log.info("Creating the XML model")
        self.doc = xml.getDOMImplementation().createDocument(None, "dll", None)
        self.top = self.doc.documentElement
        
        self.typeMap = {}
        self.typeMap['#!@#index'] = 1
        
        self.text = {}

        for (fname) in exportlist :
            self.text[fname] = 1

        sr.pulse()    

        self.xmlMap = {}
    
        self.log.info("Iterating through the AST")
        self.parseXML(ast, self.top, None, 0)
        sr.pulse()
        self.log.info("Finished iterating through AST and generating XML content")
            
        self.log.info("Added %d functions out of %d possible functions in the DLL to the XML file", self.numFuncIncluded, len(exportlist))
        
        basedir = self.cfg.get('directories', 'basedir')
        yaccpath = os.path.join(basedir, 'yacctab.py')
            
        try:
            os.remove(yaccpath)
        except:
            pass
            
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