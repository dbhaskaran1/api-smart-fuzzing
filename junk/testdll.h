/*
 * TestDLL.h
 *
 *  Created on: Oct 18, 2011
 *      Author: Rob
 */

#ifndef TESTDLL_H_
#define TESTDLL_H_

#include <windows.h>

#define TESTBOOL

#ifdef TESTBOOL
#define TESTVAL 1
#else
#define TESTVAL 0
#endif

int global_1 = TESTVAL;
char global_2 = 'A';

typedef enum DAY{
	WORKDAY,
	WEEKDAY
} day;

typedef unsigned int unsigned_int;
typedef unsigned_int uint;

typedef struct type1{
	char a;
	short b;
	double c;
	char d;
} Type1;

typedef union type2{
	char a;
	short b;
	double c;
	char d;
} Type2;

typedef struct structwrapper{
	Type1 a;
	char b;
	Type2 c;
} StructWrapper;

typedef union unionwrapper{
	Type1 a;
	char b;
	Type2 c;
} UnionWrapper;

typedef struct mutual1 Mutual1;
typedef struct mutual2 Mutual2;

struct mutual1{
	uint ** a;
	Mutual2 * b;
};

struct mutual2{
	int * a;
	Mutual1 * b;
};

typedef struct linkedlist LinkedList;

struct linkedlist{
	int index;
	LinkedList * next;
	LinkedList * prev;
	void * data;
};

__declspec (dllexport) int write(long *, long);
__declspec (dllexport) int overflow(int, char);
__declspec (dllexport) int testone(char, Type1, Type2);
__declspec (dllexport) int testtwo(StructWrapper, UnionWrapper);
__declspec (dllexport) int testthree(long *, long*);
__declspec (dllexport) int testfour(long *, unsigned short*);
__declspec (dllexport) int testfive(long ***, unsigned short **);
__declspec (dllexport) int testsix(Type1 *, Type1 *);
__declspec (dllexport) int testseven(Type1 *, Type2 *);
__declspec (dllexport) int testeight(Mutual1);
__declspec (dllexport) int testnine(LinkedList *);
__declspec (dllexport) int testten();

#endif /* TESTDLL_H_ */
