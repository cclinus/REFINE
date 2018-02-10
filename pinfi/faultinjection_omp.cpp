#include "faultinjection.h"
#include <string.h>
#include <assert.h>
#include <stdio.h>
#include "pin.H"

#include "mt64.h"
#include "utils.h"
#include "instselector.h"
#include <inttypes.h>

#define MAX_THREADS 256
static INT32 fi_inject_thread = -1;
static UINT64 fi_iterator[MAX_THREADS] __attribute__((aligned(64))) =  { 0 };

VOID inject_Reg(THREADID tid, VOID *ip, UINT32 op, REG reg, PIN_REGISTER *val) {
    fi_iterator[tid]++;

    if(fi_inject_thread != tid)
        return;

    if(fi_iterator[tid] != fi_index)
        return;

    // XXX: !!! CAUTION !!! WARNING !!! CALLING PIN_Detach breaks injection that changes
    // registers. It seems Pin does not transfer the changed state after detaching
#if 0 // FAULTY
    if(fi_iterator[tid] > fi_index) {
        // XXX: One fault per run, thus remove instr. and detach to speedup execution
        // This can be changed to allow multiple errors
        PIN_RemoveInstrumentation();
        PIN_Detach();
        return;
    }
#endif

    if(action == DO_RANDOM) {
        UINT32 size_bits = REG_Size(reg)*8;
        fi_bit_flip = genrand64_int64()%size_bits;
    }

    UINT32 inject_byte = fi_bit_flip/8;
    UINT32 inject_bit = fi_bit_flip%8;

    fi_output_fstream << "thread=" << tid << ", fi_index=" << fi_iterator[tid] << ", op=" << op
        << ", reg=" << REG_StringShort(reg) << ", bitflip=" << fi_bit_flip << ", addr=" << hexstr(ip) << std::endl;

    cerr << "INJECT thread=" << tid << ", fi_index=" << fi_iterator[tid] << ", op=" << op
        << ", reg=" << REG_StringShort(reg) << ", bitflip=" << fi_bit_flip << ", addr=" << hexstr(ip) << std::endl;

#if VERBOSE
    LOG("Instruction:" + ptrstr(ip) +", reg " + REG_StringShort(reg) + ", val ");
    for(UINT32 i = 0; i<REG_Size(reg); i++)
        LOG(hexstr(val->byte[i]) + " ");
#endif

    val->byte[inject_byte] = (val->byte[inject_byte] ^ (1U << inject_bit));

#if VERBOSE
    LOG(" bitflip:" + decstr(bit_flip) +", reg " + REG_StringShort(reg) + ", val ");
    for(UINT32 i = 0; i<REG_Size(reg); i++)
        LOG(hexstr(val->byte[i]) + " ");
    LOG("\n");
#endif
}

// XXX: CAUTION: Globals for mem injection assume single-threaded execution
// TODO: Use per-thread data instead of globals
VOID *g_ip = 0;
VOID *g_mem_addr = 0;
UINT32 g_size = 0;

// XXX TODO FIXME: add operand number to mem destinations
VOID inject_Mem(THREADID tid, VOID *ip) {
    fi_iterator[tid]++;
    if(fi_inject_thread != tid)
        return;
    if(fi_iterator[tid] != fi_index)
        return;
    // XXX: !!! CAUTION !!! WARNING !!! CALLING PIN_Detach breaks injection that changes
    // registers. It seems Pin does not transfer the changed state after detaching
#if 0 // FAULTY
    if(fi_iterator[tid] > fi_index) {
        // XXX: One fault per run, thus remove instr. and detach to speedup execution
        // This can be changed to allow multiple errors
        PIN_RemoveInstrumentation();
        PIN_Detach();
        return;
    }
#endif

    assert(ip == g_ip && "Analyze ip unequal to inject ip!\n");
    UINT8 *p = (UINT8 *) g_mem_addr;
#ifdef VERBOSE
    LOG("Instruction: " + ptrstr(ip) +", memory " + ptrstr(g_mem_addr) + ", ");
    LOG("hex: ");
    for(UINT32 i = 0; i<g_size; i++)
        LOG(hexstr(*(p + i)) + " ");
    LOG("\n");
#endif

    UINT32 size_bits = g_size*8;

    UINT32 bit_flip = genrand64_int64()%size_bits;
    UINT32 inject_byte = bit_flip/8;
    UINT32 inject_bit = bit_flip%8;

    fi_output_fstream << "fi_index=" << fi_iterator[tid] << ", mem_addr=" << hexstr(g_mem_addr)
        << ", bitflip=" << bit_flip << ", addr=" << hexstr(ip) << std::endl;

    *(p + inject_byte) = (*(p + inject_byte) ^ (1U << inject_bit));

#ifdef VERBOSE
    LOG(" bitflip:" + decstr(bit_flip) +" ");
    LOG("hex: ");
    for(UINT32 i = 0; i<g_size; i++)
        LOG(hexstr(*(p + i)) + " ");
    LOG("\n");
#endif
}

VOID analyze_Mem(VOID *ip, VOID *mem_addr, UINT32 size) {
    g_ip = ip;
    g_mem_addr = mem_addr;
    g_size = size;
}

VOID instruction_Instrumentation(INS ins, VOID *v) {
    // decides where to insert the injection calls and what calls to inject
    if (!isValidInst(ins))
        return;

    int fi_op = 0;

    struct {
        enum OP_TYPE type;
        REG reg;
    } FI_Ops[MAX_OPS];
    int numOps = 0;

    REG reg;

#ifdef VERBOSE
    LOG("==============\n");
    LOG("Checking: " + hexstr(INS_Address(ins)) + " \"" + INS_Disassemble(ins) + "\", ");
#endif
#ifdef FI_SRC_REG
    int numR = INS_MaxNumRRegs(ins);
    for(int i = 0; i<numR; i++) {
        if(!REGx_IsInstrPtr(INS_RegR(ins, i))) {
            FI_Ops[numOps].type = REG_SRC;
            FI_Ops[numOps].reg = INS_RegR(ins, i);
#ifdef VERBOSE
            LOG("regR " + decstr(i) + ": " + REG_StringShort(FI_Ops[numOps].reg) + ", size " + decstr(REG_Size(FI_Ops[numOps].reg)));
#endif
            numOps++;
        }
    }
#endif
#ifdef FI_DST_REG
    int numW = INS_MaxNumWRegs(ins);
    for(int i = 0; i<numW; i++) {
        // Skip IP dst: cannot modify directly IP
        // TODO: Instead, modifying IP could be achieved by using a JMP instruction
        if(!REGx_IsInstrPtr(INS_RegW(ins, i))) {
            FI_Ops[numOps].type = REG_DST;
            FI_Ops[numOps].reg = INS_RegW(ins, i);
#ifdef VERBOSE
            LOG("regW " + decstr(i) + ": " + REG_StringShort(FI_Ops[numOps].reg) + ", size " + decstr(REG_Size(FI_Ops[numOps].reg)));
#endif
            numOps++;
        }
    }
#endif
#ifdef FI_DST_MEM
    // TODO: Think about scatter/gather operations, ignore for now
    if(INS_IsMemoryWrite(ins) && INS_hasKnownMemorySize(ins)) {
        FI_Ops[numOps].type = MEM_DST;
        numOps++;
    }
#endif
#ifdef VERBOSE
    LOG("\n");
#endif

    assert((numOps > 0) && "No ops to FI!\n");

    IARG_TYPE ArgType = IARG_REG_REFERENCE;

    if(action == DO_RANDOM)
        fi_op = genrand64_int64()%numOps;

    if(FI_Ops[fi_op].type == REG_DST || FI_Ops[fi_op].type == REG_SRC) {
        reg = FI_Ops[fi_op].reg;
#ifdef VERBOSE
        LOG("FI instrumentation at: " + REG_StringShort(reg) + ", " + (FI_Ops[fi_op].type == REG_SRC?"SRC":"DST") + "\n");
#endif

        IPOINT IPoint;
        if(FI_Ops[fi_op].type == REG_SRC || INSx_MayChangeControlFlow(ins))
            IPoint = IPOINT_BEFORE;
        else
            IPoint = IPOINT_AFTER;

        INS_InsertPredicatedCall(ins, IPoint, AFUNPTR(inject_Reg),
                IARG_THREAD_ID,
                IARG_ADDRINT, INS_Address(ins),
                IARG_UINT32, fi_op,
                IARG_UINT32, reg,
                ArgType , reg,
                IARG_END);

    }
    // Inject to MEM
    // XXX: Address can be resolved only at IPOINT_BEFORE. Split fault injection: 1) analyze to
    // get the address and size, and 2) injecton happens at the next instruction (if possible)
    else if(FI_Ops[fi_op].type == MEM_DST) {
        // XXX: CALL instructions modify the stack: PUSH(IP). However they are considered non-fall 
        // through. Hence, they have no next instruction and FI is not possible
        if(INS_Next(ins) != INS_Invalid()) {
            INS_InsertPredicatedCall(ins, IPOINT_BEFORE, AFUNPTR(analyze_Mem),
                    IARG_ADDRINT, INS_Address(ins),
                    IARG_MEMORYWRITE_EA,
                    IARG_MEMORYWRITE_SIZE,
                    IARG_END);

#ifdef VERBOSE
            LOG("FI instrumentation at MEM_DST\n");
#endif
            INS_InsertPredicatedCall(INS_Next(ins), IPOINT_BEFORE, AFUNPTR(inject_Mem),
                    IARG_THREAD_ID,
                    IARG_ADDRINT, INS_Address(ins),
                    IARG_END);
        }

    }
    else
        assert(false && "FI type is invalid!\n");

#ifdef VERBOSE
    LOG("==============\n");
#endif

}

VOID get_instance_number(const char *inj_file, const char *tgt_file)
{
    FILE *fp = fopen(inj_file, "r");
    if( ( fp = fopen(inj_file, "r") ) != NULL) {
        cerr << "REPRODUCE FI" << endl;

        int ret = fscanf(fp, "thread=%d, fi_index=%llu, op=%u, reg=%*[a-z0-9], bitflip=%u, addr=%*x\n", &fi_inject_thread, &fi_index, &fi_op, &fi_bit_flip);
        fprintf(stderr, "thread=%d, fi_index=%llu, op=%u, bitflip=%u\n", fi_inject_thread, fi_index, fi_op, fi_bit_flip);
        assert(ret == 4 && "fscanf failed!\n");
        //fprintf(stderr, "thread=%d, fi_index=%llu, op=%u, reg=%s, bitflip=%u\n", fi_inject_thread, fi_index, fi_op, reg, fi_bit_flip);
        action = DO_REPRODUCE;
        assert(fi_inject_thread >= 0 && "target thread < 0!\n");
        assert(fi_index > 0 && "fi_index <= 0!\n");
    }
    else if( (fp = fopen(tgt_file, "r") ) != NULL) {
        int ret = fscanf(fp, "thread=%d, fi_index=%llu\n", &fi_inject_thread, &fi_index);
        assert(ret == 1 && "fscanf failed!\n");
        cerr << "TARGET thread=" << fi_inject_thread << ", fi_index=" << fi_index <<" GIVEN, RANDOM INJECTION TO OPERANDS" << endl;
        action = DO_RANDOM;

        fi_output_fstream.open(inj_file, std::fstream::out);
        assert(fi_output_fstream.is_open() && "Cannot open injection output file\n");
    }
    else {
        assert(false && "PINFI needs either a target or injection file\n");
    }

    fclose(fp);

    // init ranodm
    uint64_t seed;
    FILE* urandom = fopen("/dev/urandom", "r");
    fread(&seed, sizeof(seed), 1, urandom);
    fclose(urandom);
    init_genrand64(seed);
}

VOID Fini(INT32 code, VOID *v)
{
    fi_output_fstream.close();
}

/* ===================================================================== */
/* Print Help Message                                                    */
/* ===================================================================== */

INT32 Usage()
{
    PIN_ERROR( "This Pintool does fault injection\n"
            + KNOB_BASE::StringKnobSummary() + "\n");
    return -1;
}

int main(int argc, char *argv[])
{
    PIN_InitSymbols();

    if (PIN_Init(argc, argv)) return Usage();

    configInstSelector();

    get_instance_number(injection_file.Value().c_str(), target_file.Value().c_str());

    INS_AddInstrumentFunction(instruction_Instrumentation, 0);

    PIN_AddFiniFunction(Fini, 0);

    // Never returns
    PIN_StartProgram();

    return 0;
}

