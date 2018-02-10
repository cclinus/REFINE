#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include <stdint.h>
#include <inttypes.h>
#include <assert.h>
#include <execinfo.h>
#include <string.h>

void selInst(uint64_t *, uint8_t *) __attribute__((preserve_all));
void selMBB(uint64_t *, uint64_t) __attribute__((preserve_all));
void doInject(unsigned , uint64_t *, uint64_t *, uint8_t *) __attribute__((preserve_all));
void init() __attribute__((constructor));
void fini() __attribute__((destructor));

/* initializes mt[NN] with a seed */
void init_genrand64(uint64_t seed);

/* generates a random number on [0, 2^64-1]-interval */
uint64_t genrand64_int64(void);

#define NN 312
#define MM 156
#define MATRIX_A UINT64_C(0xB5026F5AA96619E9)
#define UM UINT64_C(0xFFFFFFFF80000000) /* Most significant 33 bits */
#define LM UINT64_C(0x7FFFFFFF) /* Least significant 31 bits */

/* The array for the state vector */
static uint64_t mt[NN];
/* mti==NN+1 means mt[NN] is not initialized */
static int mti=NN+1;

/* initializes mt[NN] with a seed */
void init_genrand64(uint64_t seed)
{
    mt[0] = seed;
    for (mti=1; mti<NN; mti++)
        mt[mti] =  (UINT64_C(6364136223846793005) * (mt[mti-1] ^ (mt[mti-1] >> 62)) + mti);
}

/* generates a random number on [0, 2^64-1]-interval */
uint64_t genrand64_int64(void)
{
    int i;
    uint64_t x;
    static uint64_t mag01[2]={UINT64_C(0), MATRIX_A};

    if (mti >= NN) { /* generate NN words at one time */

        /* if init_genrand64() has not been called, */
        /* a default initial seed is used     */
        if (mti == NN+1)
            init_genrand64(UINT64_C(5489));

        for (i=0;i<NN-MM;i++) {
            x = (mt[i]&UM)|(mt[i+1]&LM);
            mt[i] = mt[i+MM] ^ (x>>1) ^ mag01[(int)(x&UINT64_C(1))];
        }
        for (;i<NN-1;i++) {
            x = (mt[i]&UM)|(mt[i+1]&LM);
            mt[i] = mt[i+(MM-NN)] ^ (x>>1) ^ mag01[(int)(x&UINT64_C(1))];
        }
        x = (mt[NN-1]&UM)|(mt[0]&LM);
        mt[NN-1] = mt[MM-1] ^ (x>>1) ^ mag01[(int)(x&UINT64_C(1))];

        mti = 0;
    }

    x = mt[mti++];

    x ^= (x >> 29) & UINT64_C(0x5555555555555555);
    x ^= (x << 17) & UINT64_C(0x71D67FFFEDA60000);
    x ^= (x << 37) & UINT64_C(0xFFF7EEE000000000);
    x ^= (x >> 43);

    return x;
}

uint64_t dynFICount = 0;
uint64_t dynFIIndex = 0;
//XXX: for debug reasons
//uint64_t dynFIIndex_mbb = 0;
uint64_t dynFITarget = 0;
// default is random injection
int randomInjection = 1;
uint64_t op_num;
uint64_t op_size;
unsigned bit_pos;

const char *inscount_fname = "refine-inscount.txt";
const char *inject_fname = "refine-inject.txt";
FILE *ins_fp, *inj_fp;

void selMBB(uint64_t *ret, uint64_t num_insts)
{
    *ret = 0;
    //*ret = 1; //ggout
    //printf("Called SelMBB num_insts: %llu\n", num_insts);
    if( dynFICount && ( dynFIIndex < dynFITarget ) && dynFITarget <= ( dynFIIndex + num_insts ) ) {
        //printf("CHECKING dynFITarget %llu dynFIIndex %llu num_insts %llu\n", dynFITarget, dynFIIndex, num_insts);
        //assert(0 && "Should never happen!\n"); //ggout
        //printf("DETAILED sim\n");
        //*ret = 0;
        //printf("FI dynFIIndex %llu dynFIIndex_mbb %llu num_insts %llu\n", dynFIIndex, dynFIIndex_mbb, num_insts);
        *ret = 1;
    }
    else {
        /*printf("before dynFIIndex %llu dynFIIndex_mbb %llu num_insts %llu\n", dynFIIndex, dynFIIndex_mbb, num_insts);
          assert(dynFIIndex == dynFIIndex_mbb && "dynFIIndex != dynFIIndex_mbb");*/
        //dynFIIndex_mbb += num_insts;
        dynFIIndex += num_insts;
        //printf("after dynFIIndex %llu dynFIIndex_mbb %llu num_insts %llu\n", dynFIIndex, dynFIIndex_mbb, num_insts);
    }
}

void selInst(uint64_t *ret, uint8_t *instr_str)
{
    /*void *callstack[2];
    int frames = backtrace(callstack, 2);
    char **strs = backtrace_symbols(callstack, frames);
    int i;
    for(i=0; i<frames; i++)
        printf("%s\n", strs[i]);
    free(strs);
    assert(0 && "early abort first");*/
    *ret = 0;
    dynFIIndex++;
    /*void *callstack[2];
    int frames = backtrace(callstack, 2);
    char **strs = backtrace_symbols(callstack, frames);
    if(strstr(strs[1], "vranlc") != NULL)*/
    //printf("%llu %s\n", dynFIIndex, instr_str);
    /*free(strs);*/

    //return; // ggout

    if( dynFICount && ( dynFIIndex == dynFITarget ) ){
        *ret = 1;
        printf("INJECT %llu %s\n", dynFIIndex, instr_str);
        //assert(0 && "early abort"); //ggout
    }
}

void doInject(unsigned num_ops, uint64_t *op, uint64_t *size, uint8_t *bitmask)
{
    unsigned bitflip;
    if(randomInjection) {
        printf("DO RANDOM INJECTION!\n");
        *op = genrand64_int64()%num_ops;

        // XXX: size is in bytes, multiply by 8 for bits
        bitflip = (genrand64_int64()%(8*size[*op]));

        unsigned i;
        for(i=0; i<size[*op]; i++)
            bitmask[i] = 0;

        unsigned bit_i = bitflip/8;
        unsigned bit_j = bitflip%8;

        bitmask[bit_i] = (1U << bit_j);

        // Write random injection specifics to file
        fprintf(inj_fp, "fi_index=%"PRIu64", op=%"PRIu64", size=%"PRIu64", bitflip=%u\n", dynFIIndex, *op, size[*op], bitflip);
        fflush(inj_fp);
    }
    else {
        printf("DO REPRODUCIBLE INJECTION!\n");
        *op = op_num;
        bitflip = bit_pos;

        printf("op_size %llu size[*op] %llu\n", op_size, size[*op]);
        assert( ( op_size == size[*op] ) && "op_size != size[*op]");
        unsigned i;
        for(i=0; i<op_size; i++)
            bitmask[i] = 0;

        unsigned bit_i = bitflip/8;
        unsigned bit_j = bitflip%8;

        bitmask[bit_i] = (1U << bit_j);
    }

    printf("INJECTING FAULT: fi_index=%"PRIu64", op=%"PRIu64", size=%"PRIu64", bitflip=%u\n", dynFIIndex, *op, size[*op], bitflip);
    fflush(stdout);
}

void init()
{
    uint64_t seed;
    FILE *fp = fopen("/dev/urandom", "r");
    assert(fp != NULL && "Error opening /dev/urandom\n");
    fread(&seed, sizeof(seed), 1, fp);
    init_genrand64(seed);
    assert(ferror(fp) == 0 && "Error reading /dev/urandom\n");
    fclose(fp);

    ins_fp = fopen(inscount_fname, "r");
    if(ins_fp) {
        fscanf(ins_fp, "%"PRIu64"\n", &dynFICount);
        assert(dynFICount > 0 && "dynFICount is invalid!\n");

        inj_fp = fopen(inject_fname, "r");
        // reproduce injection
        if(inj_fp) {
            printf("REPRODUCE INJECTION\n");
            fscanf(inj_fp, "fi_index=%"PRIu64", op=%"PRIu64", size=%"PRIu64", bitflip=%u\n", &dynFITarget, &op_num, &op_size, &bit_pos);
            assert(dynFITarget > 0 && "dynFITarget <= 0!\n");
            assert(op_num >= 0 && "op_num < 0!\n");
            assert(op_size > 0 && "op_size <=0!\n");
            assert(bit_pos >= 0 && "bit_pos < 0!\n");
            randomInjection = 0;
        }
        // create random injection target
        else {
            printf("RANDOM INJECTION\n");
            // Instruction count starts from 1
            dynFITarget = (genrand64_int64()%dynFICount) + 1;
            printf("TARGET %llu\n", dynFITarget);
            inj_fp = fopen(inject_fname, "w");
            assert(inj_fp != NULL && "Error opening output file\n");
        }
    }
}

void fini()
{
    if(dynFICount) {
        fclose(inj_fp);
        fclose(ins_fp);
    }
    else {
        fprintf(stderr, "PROFILING: dynamic count of FI instructions: %"PRIu64"\n", dynFIIndex);
        ins_fp = fopen(inscount_fname, "w");
        assert(ins_fp != NULL && "Error opening inscount file\n");
        /*if(dynFIIndex_mbb) {
            printf("dynFIIndex %llu dynFIIndex_mbb %llu\n", dynFIIndex, dynFIIndex_mbb); //ggout
            assert(dynFIIndex == dynFIIndex_mbb && "dynFIIndex from selInst and selMBB differ!\n");
        }*/
        fprintf(ins_fp, "%"PRIu64"\n", dynFIIndex);
        fclose(ins_fp);
    }
}

