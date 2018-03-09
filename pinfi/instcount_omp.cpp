#include<iostream>
#include<fstream>

#include <set>
#include <map>
#include <string>

#include <assert.h>

#include "pin.H"
#include "utils.h"
#include "instselector.h"

KNOB<string> instcount_file(KNOB_MODE_WRITEONCE, "pintool",
    "o", "pin.instcount.txt", "specify instruction count file name");

KNOB<bool> save_instr(KNOB_MODE_WRITEONCE, "pintool",
    "save-instr", "0", "shows details of the instruction instrumentation");

KNOB<string> instrument_file(KNOB_MODE_WRITEONCE, "pintool",
    "instr-file", "pin.instrument.txt", "shows details of the instruction instrumentation");

#define MAX_THREADS 256
// 64B alignment TODO: use sysconf or similar to set padding at runtime
static union { UINT64 v; char pad[64]; } fi_iterator[MAX_THREADS] __attribute__((aligned(64))) = { 0 };
//static UINT64 fi_iterator_atomic = 0;
int gtid = 0;

std::fstream instrument_ofstream;

VOID countInst(THREADID tid, UINT32 c)
{
  fi_iterator[tid].v += c;
  //__atomic_add_fetch(&fi_iterator_atomic, c, __ATOMIC_SEQ_CST);
}

// Pin calls this function every time a new instruction is encountered
VOID CountInst(TRACE trace, VOID *v)
{
  if(isValidTrace(trace))
    for( BBL bbl = TRACE_BblHead(trace); BBL_Valid(bbl); bbl = BBL_Next(bbl) ) {
      int num_insts = 0;
      // Insert a call to countInst before every bbl, passing the number of target FI instructions
      for(INS ins = BBL_InsHead(bbl); INS_Valid(ins); ins = INS_Next(ins) )
        if(isValidInst(ins)) {
          num_insts++;

          if(save_instr.Value())
            instrument_ofstream << "img=" << IMG_Name(SEC_Img(RTN_Sec(INS_Rtn(ins)))) << ", addr=" << hexstr(INS_Address(ins))
              << ", instr=\"" << INS_Disassemble(ins) << "\"" << std::endl;
        }

      if(num_insts > 0) {
        BBL_InsertCall(bbl, IPOINT_BEFORE, (AFUNPTR)countInst, IARG_THREAD_ID, IARG_UINT32, num_insts, IARG_END);
        //cerr << "Found BBL at " << std::hex << "0x" << BBL_Address(bbl) << " - " << "0x" << ( BBL_Address(bbl) + BBL_Size(bbl) ) << endl;
      }
    }
}

VOID ThreadStart(THREADID tid, CONTEXT *ctx, INT32 flags, VOID *v)
{
  //gtid++;
  __atomic_fetch_add(&gtid, 1, __ATOMIC_SEQ_CST);
}

VOID Fini(INT32 code, VOID *v)
{
  // Write to a file since cout and cerr maybe closed by the application
  ofstream OutFile;
  OutFile.open(instcount_file.Value().c_str());
  OutFile.setf(ios::showbase);
  UINT64 sum = 0;
  for(int i = 0; i < gtid; i++) {
    OutFile << "thread=" << i << ", fi_index=" << fi_iterator[i].v << endl;
    sum += fi_iterator[i].v;
  }
  OutFile << "fi_index=" << sum << endl;
  OutFile.close();

  //cerr << "Sum: " << sum << " -- atomic: " << fi_iterator_atomic << "\n";
  cerr << "Sum: " << sum << "\n";

  if(save_instr.Value())
    instrument_ofstream.close();
}

/* ===================================================================== */
/* Print Help Message                                                    */
/* ===================================================================== */

INT32 Usage()
{
  cerr << "This tool counts the number of dynamic instructions executed" << endl;
  cerr << endl << KNOB_BASE::StringKnobSummary() << endl;
  return -1;
}

int main(int argc, char * argv[])
{
  PIN_InitSymbols();
  // Initialize pin
  if (PIN_Init(argc, argv)) return Usage();

  //configInstSelector();

  if(save_instr.Value()) {
    instrument_ofstream.open(instrument_file.Value().c_str(), std::fstream::out);
    assert(instrument_ofstream.is_open() && "Cannot open instrumentation output file\n");
  }

  PIN_AddThreadStartFunction(ThreadStart, 0);
  // Register CountInst to be called to instrument instructions in a trace
  TRACE_AddInstrumentFunction(CountInst, 0);

  // Register Fini to be called when the application exits
  PIN_AddFiniFunction(Fini, 0);

  // Start the program, never returns
  PIN_StartProgram();

  return 0;
}
