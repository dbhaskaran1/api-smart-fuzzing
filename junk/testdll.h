/*
 * TestDLL.h
 *
 *  Created on: Oct 18, 2011
 *      Author: Rob
 */

#ifndef TESTDLL_H_
#define TESTDLL_H_

#include <windows.h>

BOOL WINAPI DllMain(HINSTANCE hinstDLL,DWORD,LPVOID);
_declspec (dllexport) long  add_num(long, long);
_declspec (dllexport) long  sub_num(long, long);

#endif /* TESTDLL_H_ */
