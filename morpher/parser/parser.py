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
           
        pipe = Popen(   path_list, 
                        stdout=PIPE, 
                        universal_newlines=True)
        text = pipe.communicate()[0]
            
        # Make the output pycparser compatible
        text = re.sub('__stdcall',"",text)
        text = re.sub('__attribute__\(\(.*?\)\)*',"",text)
        text = re.sub('#.*',"",text)
        
        parser = CParser(lex_optimize=False, yacc_debug=False, yacc_optimize=False)
    
        return parser.parse(text, self.targetfile)

    def parseXML(self, ast, element, doc, name, typeMap, state, text):
        """ 
            Fill in data!!
        """
    
        funcName = ast.__class__.__name__
    
        if funcName == "Decl":
            # Declaration of an object - get the name and pass it on!
            for c in ast.children():                                
                val = self.parseXML(c, element, doc, getattr(ast, ast.attr_names[0]), typeMap, state, text)            
                return val
        elif funcName == "FuncDecl":
            # Function Declaration - Take input from the Decl node for the name, and explore all sub-nodes
            func = doc.createElement("function")
            func.setAttribute("name", name)
            for c in ast.children():            
                val = self.parseXML(c, func, doc, name, typeMap, state, text)    
            if state == 1:                                                         
                element.appendChild(func)
            return None 
        elif funcName == "ParamList":
            # The parameter list! List all the parameters!!
            for c in ast.children():
                param = doc.createElement("param")
                val = self.parseXML(c, param, doc, name, typeMap, state, text)
                if val != None:
                    param.setAttribute("type", val)
                if state == 1:
                    element.appendChild(param) 
        elif funcName == "PtrDecl":
            for c in ast.children():
                val = self.parseXML(c, element, doc, name, typeMap, state, text)
                if val != None:
                    return "P" + val
        elif funcName == "TypeDecl":
            for c in ast.children():
                val = self.parseXML(c, element, doc, name, typeMap, state, text)
                if val != None:
                    return val
        elif funcName == "Typename":
            for c in ast.children():
                val = self.parseXML(c, element, doc, name, typeMap, state, text)
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
                elif val[0] in typeMap:
                    iterMap = typeMap[val[0]]
                    while len(iterMap) > 2 and iterMap[0:2] == "//":
                        if iterMap[2:] in typeMap:
                            iterMap = typeMap[str(iterMap[2:])]
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
                val = self.parseXML(c, element, doc, name, typeMap, state, text)
                if val != None:
                    #param = doc.createElement("param")
                    #param.setAttribute("type", val)
                    #type.appendChild(param)
                    typeMap[getattr(ast, ast.attr_names[0])] = val
            #element.appendChild(type)
            return None 
        elif funcName == "Struct":
            if getattr(ast, ast.attr_names[0]) not in typeMap:
                ind = typeMap['#!@#index']
                typeMap['#!@#index'] = typeMap['#!@#index'] + 1
            else:
                ind = typeMap[getattr(ast, ast.attr_names[0])]
                
            changed = 0
    
            typex = doc.createElement("usertype")
            #type.setAttribute("name", getattr(ast, ast.attr_names[0]))
            typex.setAttribute("id", str(ind))
            typex.setAttribute("type", "struct")
            for c in ast.children():
                val = self.parseXML(c, typex, doc, name, typeMap, state, text)
                if val != None:
                    param = doc.createElement("param")
                    param.setAttribute("type", val)
                    typex.appendChild(param)
                    typeMap[getattr(ast, ast.attr_names[0])] = str(ind)
                    changed = 1
            if changed == 1:
                if state == 1:
                    element.appendChild(typex)
                return str(ind)
            else:
                if getattr(ast, ast.attr_names[0]) not in typeMap:
                    typeMap['#!@#index'] = typeMap['#!@#index'] - 1
                return "//"+getattr(ast, ast.attr_names[0])
            #else:
            #   return str(typeMap[getattr(ast, ast.attr_names[0])])
        elif funcName == "Union":
            if getattr(ast, ast.attr_names[0]) not in typeMap:
                ind = typeMap['#!@#index']
                typeMap['#!@#index'] = typeMap['#!@#index'] + 1
            else:
                ind = typeMap[getattr(ast, ast.attr_names[0])]
                
            changed = 0
    
            typex = doc.createElement("usertype")
            #type.setAttribute("name", getattr(ast, ast.attr_names[0]))
            typex.setAttribute("id", str(ind))
            typex.setAttribute("type", "union")
            for c in ast.children():
                val = self.parseXML(c, typex, doc, name, typeMap, state, text)
                if val != None:
                    param = doc.createElement("param")
                    param.setAttribute("type", val)
                    typex.appendChild(param)
                    typeMap[getattr(ast, ast.attr_names[0])] = str(ind)
                    changed = 1
            if changed == 1:
                if state == 1:
                    element.appendChild(typex)
                return str(ind)
            else:
                if getattr(ast, ast.attr_names[0]) not in typeMap:
                    typeMap['#!@#index'] = typeMap['#!@#index'] - 1
                return "//"+getattr(ast, ast.attr_names[0])
            #else:
            #    return str(typeMap[name])
        elif funcName == "Enum":
            return "i"
        elif funcName == "Constant":
            for c in ast.children():
                val = self.parseXML(c, element, doc, None, typeMap, state, text)
            return "["+getattr(ast, ast.attr_names[1])+"]"
        elif funcName == "ArrayDecl":
            val = ""
            for c in ast.children():
                getVal = self.parseXML(c, element, doc, None, typeMap, state, text)
                if getVal != None:
                    val += getVal
            return val
        else:
            val = ""
            for c in ast.children():
                val = self.parseXML(c, element, doc, None, typeMap, state, text)
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
        text = open(self.targetfile, 'rU').read()
    
        # Create the XML tree    
        self.log.info("Creating the XML model")
        doc = xml.getDOMImplementation().createDocument(None, "dll", None)
        top = doc.documentElement
        
        typeMap = {}
        typeMap['#!@#index'] = 1
    
        self.parseXML(ast, top, doc, None, typeMap, 0, text)
        sr.pulse()
        self.parseXML(ast, top, doc, None, typeMap, 1, text)
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
            xmlstr = top.toprettyxml(indent="    ", newl="\n")
            self.log.debug("\n\nXML Tree:\n%s\n", xmlstr)
        try :
            f = open(modelpath, mode="w")
        except :
            msg = "Couldn't open %s"
            self.log.exception(msg, modelpath)
            raise Exception(msg % modelpath)
        top.writexml(f, addindent="    ", newl="\n")
        f.close()
        sr.pulse()