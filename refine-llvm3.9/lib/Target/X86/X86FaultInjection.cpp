#include "X86InstrInfo.h"
#include "X86Subtarget.h"
#include "X86FaultInjection.h"
#include "X86MachineFunctionInfo.h"
#include "llvm/Target/TargetInstrInfo.h"
#include "llvm/CodeGen/MachineRegisterInfo.h"
#include "llvm/CodeGen/MachineBasicBlock.h"
#include "llvm/CodeGen/MachineModuleInfo.h"
#include "X86InstrBuilder.h"

using namespace llvm;

/* TODO: 
 * 1. Do liveness analysis to reduce context saving, check X86InstrInfo.cpp:4662
 */

// XXX: slowdown for storing string
//#define INSTR_PRINT

// Offset globals
int RSPOffset = 0, RBPOffset = -8, RAXOffset = -16;

int StackOffset = 0;

// XXX: emitPushReg and others assume starting from a 16B aligned stack
void emitPushReg(MachineBasicBlock &MBB, MachineBasicBlock::iterator I, const MCPhysReg Reg)
{
    MachineFunction &MF = *MBB.getParent();
    const TargetInstrInfo &TII = *MF.getSubtarget().getInstrInfo();

    BuildMI(MBB, I, DebugLoc(), TII.get(X86::PUSH64r)).addReg(Reg);
    StackOffset -= 8;
    dbgs() << "emitPushReg StackOffset: " << StackOffset << "\n"; //ggout
}

void emitPopReg(MachineBasicBlock &MBB, MachineBasicBlock::iterator I, const MCPhysReg Reg)
{
    MachineFunction &MF = *MBB.getParent();
    const TargetInstrInfo &TII = *MF.getSubtarget().getInstrInfo();

    BuildMI(MBB, I, DebugLoc(), TII.get(X86::POP64r)).addReg(Reg);
    StackOffset += 8;
    dbgs() << "emitPushReg StackOffset: " << StackOffset << "\n"; //ggout
}

void emitPushContextRegs(MachineBasicBlock &MBB, MachineBasicBlock::iterator I)
{
    // XXX: Push context, dynamic linker doesn't preserve volatile regs
    MachineFunction &MF = *MBB.getParent();
    const TargetInstrInfo &TII = *MF.getSubtarget().getInstrInfo();

    BuildMI(MBB, I, DebugLoc(), TII.get(X86::PUSH64r)).addReg(X86::RSI);
    BuildMI(MBB, I, DebugLoc(), TII.get(X86::PUSH64r)).addReg(X86::RDI);
    BuildMI(MBB, I, DebugLoc(), TII.get(X86::PUSH64r)).addReg(X86::RCX);
    BuildMI(MBB, I, DebugLoc(), TII.get(X86::PUSH64r)).addReg(X86::RDX);
    BuildMI(MBB, I, DebugLoc(), TII.get(X86::PUSH64r)).addReg(X86::R8);
    BuildMI(MBB, I, DebugLoc(), TII.get(X86::PUSH64r)).addReg(X86::R9);
    BuildMI(MBB, I, DebugLoc(), TII.get(X86::PUSH64r)).addReg(X86::R10);
    BuildMI(MBB, I, DebugLoc(), TII.get(X86::PUSH64r)).addReg(X86::R11);
    StackOffset -= (8*8);
    dbgs() << "emitPushCtx StackOffset: " << StackOffset << "\n"; //ggout

}

void emitPopContextRegs(MachineBasicBlock &MBB, MachineBasicBlock::iterator I)
{
    MachineFunction &MF = *MBB.getParent();
    const TargetInstrInfo &TII = *MF.getSubtarget().getInstrInfo();

    BuildMI(MBB, I, DebugLoc(), TII.get(X86::POP64r)).addReg(X86::R11);
    BuildMI(MBB, I, DebugLoc(), TII.get(X86::POP64r)).addReg(X86::R10);
    BuildMI(MBB, I, DebugLoc(), TII.get(X86::POP64r)).addReg(X86::R9);
    BuildMI(MBB, I, DebugLoc(), TII.get(X86::POP64r)).addReg(X86::R8);
    BuildMI(MBB, I, DebugLoc(), TII.get(X86::POP64r)).addReg(X86::RDX);
    BuildMI(MBB, I, DebugLoc(), TII.get(X86::POP64r)).addReg(X86::RCX);
    BuildMI(MBB, I, DebugLoc(), TII.get(X86::POP64r)).addReg(X86::RDI);
    BuildMI(MBB, I, DebugLoc(), TII.get(X86::POP64r)).addReg(X86::RSI);

    StackOffset += (8*8);
    dbgs() << "emitPopCtx StackOffset: " << StackOffset << "\n"; //ggout
}

void emitAlignStack16B(MachineBasicBlock &MBB, MachineBasicBlock::iterator I)
{
    // Save frame registers (RSP, RBP, RAX), use RBP for addressing RSPOffset, RBPOffset, RAXOffset
    MachineFunction &MF = *MBB.getParent();
    const TargetInstrInfo &TII = *MF.getSubtarget().getInstrInfo();

    BuildMI(MBB, I, DebugLoc(), TII.get(X86::AND64ri8), X86::RSP).addReg(X86::RSP).addImm(-16);
}

void emitSaveFrameFlags(MachineBasicBlock &MBB, MachineBasicBlock::iterator I)
{
    MachineFunction &MF = *MBB.getParent();
    const TargetInstrInfo &TII = *MF.getSubtarget().getInstrInfo();
    X86MachineFunctionInfo *X86MFI = MF.getInfo<X86MachineFunctionInfo>();

    // Stay clear of the red zone, 128 bytes
    // XXX: This MUST be done even FI in RSP, it will be adjusted anyway at PostFIMBB
    if(X86MFI->getUsesRedZone())
        // LEA to adjust RSP (does not clobber flags)
        addRegOffset(BuildMI(MBB, I, DebugLoc(), TII.get(X86::LEA64r), X86::RSP), X86::RSP, false, -128);

    // PUSH RSP
    BuildMI(MBB, I, DebugLoc(), TII.get(X86::PUSH64r)).addReg(X86::RSP);
    // PUSH RBP
    BuildMI(MBB, I, DebugLoc(), TII.get(X86::PUSH64r)).addReg(X86::RBP);
    // RBP <- original RSP 
    addRegOffset(BuildMI(MBB, I, DebugLoc(), TII.get(X86::LEA64r), X86::RBP), X86::RSP, false, -RBPOffset);

    // XXX: We have to store EFLAGS, they may be live during the execution of this BB
    // PUSH RAX used for saving flags, required by LAHF/SAHF instructions
    BuildMI(MBB, I, DebugLoc(), TII.get(X86::PUSH64r)).addReg(X86::RAX);
    // STORE flags
    BuildMI(MBB, I, DebugLoc(), TII.get(X86::SETOr), X86::AL);
    BuildMI(MBB, I, DebugLoc(), TII.get(X86::LAHF));
}

void emitRestoreFrameFlags(MachineBasicBlock &MBB, MachineBasicBlock::iterator I)
{
    MachineFunction &MF = *MBB.getParent();
    const TargetInstrInfo &TII = *MF.getSubtarget().getInstrInfo();
    X86MachineFunctionInfo *X86MFI = MF.getInfo<X86MachineFunctionInfo>();

    // Restore EFLAGS
    BuildMI(MBB, I, DebugLoc(), TII.get(X86::ADD8ri), X86::AL).addReg(X86::AL).addImm(INT8_MAX);
    BuildMI(MBB, I, DebugLoc(), TII.get(X86::SAHF));
    addRegOffset(BuildMI(MBB, I, DebugLoc(), TII.get(X86::MOV64rm), X86::RAX), X86::RBP, false, RAXOffset);
    addRegOffset(BuildMI(MBB, I, DebugLoc(), TII.get(X86::MOV64rm), X86::RSP), X86::RBP, false, RSPOffset);
    // Restore RBP last 
    addRegOffset(BuildMI(MBB, I, DebugLoc(), TII.get(X86::MOV64rm), X86::RBP), X86::RBP, false, RBPOffset);
    if(X86MFI->getUsesRedZone())
        // LEA adjust SP
        addRegOffset(BuildMI(MBB, I, DebugLoc(), TII.get(X86::LEA64r), X86::RSP), X86::RSP, false, 128);
}

int64_t emitAllocateStackAlign16B(MachineBasicBlock &MBB, MachineBasicBlock::iterator I, int64_t size)
{
    MachineFunction &MF = *MBB.getParent();
    const TargetInstrInfo &TII = *MF.getSubtarget().getInstrInfo();

    int64_t Offset = -StackOffset;
    Offset += size;

    int64_t AlignedStackSize = size + ( (Offset%16) > 0 ? (16 - (Offset%16)) : 0 );

    addRegOffset(BuildMI(MBB, I, DebugLoc(), TII.get(X86::LEA64r), X86::RSP), X86::RSP, false, -AlignedStackSize);

    StackOffset -= AlignedStackSize;
    dbgs() << "emitAllocStack StackOffset: " << StackOffset << "\n"; //ggout

    return AlignedStackSize;
}


void emitDeallocateStack(MachineBasicBlock &MBB, MachineBasicBlock::iterator I, int64_t size)
{
    MachineFunction &MF = *MBB.getParent();
    const TargetInstrInfo &TII = *MF.getSubtarget().getInstrInfo();

    addRegOffset(BuildMI(MBB, I, DebugLoc(), TII.get(X86::LEA64r), X86::RSP), X86::RSP, false, size);

    StackOffset += size;
    dbgs() << "emitFreeStack StackOffset: " << StackOffset << "\n"; //ggout
}

void X86FaultInjection::injectMachineBasicBlock(
        MachineBasicBlock &SelMBB,
        MachineBasicBlock &JmpDetachMBB,
        MachineBasicBlock &JmpFIMBB,
        MachineBasicBlock &OriginalMBB,
        MachineBasicBlock &CopyMBB,
        uint64_t TargetInstrCount) const
{
    MachineFunction &MF = *SelMBB.getParent();
    const TargetInstrInfo &TII = *MF.getSubtarget().getInstrInfo();
    const X86Subtarget &Subtarget = MF.getSubtarget<X86Subtarget>();

    /* ============================================================= CREATE SelMBB ========================================================== */

    {
        emitSaveFrameFlags( SelMBB, SelMBB.end() ); //ggetest
    }

    // XXX: Stack must be 16-byte aligned before calling a function. We don't know what's the alignment
    // before the call, so we do a double push scheme of RSP to align and restore it. Plus, PXOR for FI 
    // needs memory 16-byte aligned too. Align SP on a 16-byte boundary
    {
        emitAlignStack16B( SelMBB, SelMBB.end() );
    }

    {
        emitPushContextRegs( SelMBB, SelMBB.end() );
        // PUSH RDI for selMBB arg1 (pointer stack, inject flag)
        emitPushReg(SelMBB, SelMBB.end(), X86::RDI);
        // PUSH RSI for selMBB arg2 (value, number of instruction)
        //BuildMI(SelMBB, SelMBB.end(), DebugLoc(), TII.get(X86::PUSH64r)).addReg(X86::RSI);
        emitPushReg(SelMBB, SelMBB.end(), X86::RSI);

        // MOV RSI <= MBB.size(), selMBB arg2 (uint64_t, number of instructions)
        BuildMI(SelMBB, SelMBB.end(), DebugLoc(), TII.get(X86::MOV64ri), X86::RSI).addImm(TargetInstrCount);
        // Allocate stack space for arg1
        //addRegOffset(BuildMI(SelMBB, SelMBB.end(), DebugLoc(), TII.get(X86::LEA64r), X86::RSP), X86::RSP, false, -24);
        // Allocate stack space for out arg1
        int64_t AlignedStackSize = emitAllocateStackAlign16B(SelMBB, SelMBB.end(), 8 );
        dbgs() << "AlignedStackSize:" << AlignedStackSize << "\n"; //ggout
        // MOV RDI <= RSP, selMBB arg1
        addRegOffset(BuildMI(SelMBB, SelMBB.end(), DebugLoc(), TII.get(X86::LEA64r), X86::RDI), X86::RSP, false, 0);
        int64_t RetOffset = StackOffset;

        // XXX: Create the external symbol and get target flags (e.g, X86II::MO_PLT) for linking
        MachineOperand MO = MachineOperand::CreateES("selMBB");
        MO.setTargetFlags( Subtarget.classifyGlobalFunctionReference( nullptr, *MF.getMMI().getModule() ) );
        BuildMI(SelMBB, SelMBB.end(), DebugLoc(), TII.get(X86::CALL64pcrel32)).addOperand( MO );

        // TEST for jump (see code later), XXX: THIS SETS FLAGS FOR THE JMP, be careful not to mess with them until the branch
        addDirectMem(BuildMI(SelMBB, SelMBB.end(), DebugLoc(), TII.get(X86::TEST8mi)), X86::RDI).addImm(0x2);

        emitDeallocateStack( SelMBB, SelMBB.end(), AlignedStackSize );
        emitPopReg(SelMBB, SelMBB.end(), X86::RSI);
        emitPopReg(SelMBB, SelMBB.end(), X86::RDI);
        emitPopContextRegs( SelMBB, SelMBB.end() );

        SmallVector<MachineOperand, 1> Cond;
        Cond.push_back(MachineOperand::CreateImm(X86::COND_NE));
        // XXX: "The CFG information in MBB.Predecessors and MBB.Successors must be valid before calling this function.", so add the successors
        /*SelMBB.addSuccessor(&JmpDetachMBB);
          SelMBB.addSuccessor(&JmpFIMBB);*/
        TII.InsertBranch(SelMBB, &JmpDetachMBB, &JmpFIMBB, Cond, DebugLoc());

        /*dbgs() << "SelMBB\n";
        SelMBB.dump();
        dbgs() << "====\n";
        assert(false && "CHECK!\n");*/

        // JmpDetachMBB
        {
            emitRestoreFrameFlags(JmpDetachMBB, JmpDetachMBB.end());

            /*dbgs() << "JmpDetachMBB\n";
            JmpDetachMBB.dump();
            dbgs() << "====\n";
            assert(false && "CHECK!\n");*/
        }

        // JmpFIMBB
        {
            // add test for FI
            addRegOffset(BuildMI(JmpFIMBB, JmpFIMBB.end(), DebugLoc(), TII.get(X86::TEST8mi)), X86::RSP, false, RetOffset).addImm(0x1);
            
            SmallVector<MachineOperand, 1> Cond;
            Cond.push_back(MachineOperand::CreateImm(X86::COND_E));
            // XXX: "The CFG information in MBB.Predecessors and MBB.Successors must be valid before calling this function."
            // Successors added in target-indep MCFaultInjectionPass
            TII.InsertBranch(JmpFIMBB, &OriginalMBB, &CopyMBB, Cond, DebugLoc());

            /*dbgs() << "JmpFIMBB\n";
            JmpFIMBB.dump();
            dbgs() << "====\n";
            assert(false && "CHECK!\n");*/
        }
        
        // OriginalMBB, jump from JmpFIMBB
        {
            emitRestoreFrameFlags(OriginalMBB, OriginalMBB.begin());
        }
        // CopyMBB, jump from JmpFIMBB
        {
            emitRestoreFrameFlags(CopyMBB, CopyMBB.begin());
        }
    }

    dbgs() << "StackOffset:" << StackOffset << "\n"; //ggout
    assert(StackOffset == 0 && "StackOffset must be 0\n"); //ggout ggin
    //assert(false && "CHECK!\n");
}

void X86FaultInjection::injectFault(MachineFunction &MF,
        MachineInstr &MI,
        std::vector<MCPhysReg> const &FIRegs,
        MachineBasicBlock &InstSelMBB,
        MachineBasicBlock &PreFIMBB,
        SmallVector<MachineBasicBlock *, 4> &OpSelMBBs,
        SmallVector<MachineBasicBlock *, 4> &FIMBBs,
        MachineBasicBlock &PostFIMBB) const
{
    const X86Subtarget &Subtarget = MF.getSubtarget<X86Subtarget>();
    const TargetInstrInfo &TII = *MF.getSubtarget().getInstrInfo();
    const MachineRegisterInfo &MRI = MF.getRegInfo();
    const TargetRegisterInfo &TRI = *MRI.getTargetRegisterInfo();

    // XXX: PUSHF/POPF are broken: https://reviews.llvm.org/D6629
    //assert(Subtarget.hasLAHFSAHF() && "Unsupported Subtarget: MUST have LAHF/SAHF\n");

    unsigned MaxRegSize = 0;
    // Find maximum size of target register to allocate stack space for the bitmask
    for(auto FIReg : FIRegs) {
        const TargetRegisterClass *TRC = TRI.getMinimalPhysRegClass(FIReg);
        // Size is in bytes
        unsigned RegSize = TRC->getSize();
        MaxRegSize = RegSize > MaxRegSize ? RegSize : MaxRegSize;

        //dbgs() << "FIReg:" << FIReg << ", RegName:" << TRI.getName(FIReg) << ", RegSizeBits:" << 8*RegSize<< ", ";
    }
    //dbgs() << "\n";

    assert(MaxRegSize > 0 && "MaxRegSize must be > 0\n");

    /* ============================================================= CREATE InstSelMBB ========================================================== */

    // Save frame registers (RSP, RBP, RAX), use RBP for addressing
    {
        emitSaveFrameFlags( InstSelMBB, InstSelMBB.end() );
    }

    // XXX: Stack must be 16-byte aligned before calling a function. We don't know what's the alignment
    // before the call, so we do a double push scheme of RSP to align and restore it. Plus, PXOR for FI 
    // needs memory 16-byte aligned too. Align SP on a 16-byte boundary
    {
        emitAlignStack16B( InstSelMBB, InstSelMBB.end() );
    }

    {
        emitPushContextRegs( InstSelMBB, InstSelMBB.end() );

        // PUSH RDI for selInst arg1 (pointer stack, inject flag)
        //BuildMI(InstSelMBB, InstSelMBB.end(), DebugLoc(), TII.get(X86::PUSH64r)).addReg(X86::RDI);
        emitPushReg( InstSelMBB, InstSelMBB.end(), X86::RDI );
#ifdef INSTR_PRINT
        // PUSH RSI for selInst arg2 (uint8_t *, instr_str)
        //BuildMI(InstSelMBB, InstSelMBB.end(), DebugLoc(), TII.get(X86::PUSH64r)).addReg(X86::RSI);
        emitPushReg( InstSelMBB, InstSelMBB.end(), X86::RSI );
        std::string instr_str;
        llvm::raw_string_ostream rso(instr_str);
        //MI.print(rso, true); //skip operands
        MI.print(rso); //include operands
        //dbgs() << rso.str() << "size:" << rso.str().size() << "c_str size:" << strlen(rso.str().c_str())+1 << "\n";
#endif
#ifdef INSTR_PRINT
        // out arg1 + in arg str
        int64_t size = 8 + rso.str().size()+1/*str size + 1 for NUL char*/;
#else
        // out arg1
        int64_t size = 8;
#endif
        int64_t AlignedStackSize = emitAllocateStackAlign16B( InstSelMBB, InstSelMBB.end(), size );
        // MOV RDI <= RSP, selInst out arg1
        addRegOffset(BuildMI(InstSelMBB, InstSelMBB.end(), DebugLoc(), TII.get(X86::LEA64r), X86::RDI), X86::RSP, false, 0);
#ifdef INSTR_PRINT
        // LEA RSI <= &op, doInject arg2 (uint64_t *, &op, 8B), 8 is the offset from arg1
        addRegOffset(BuildMI(InstSelMBB, InstSelMBB.end(), DebugLoc(), TII.get(X86::LEA64r), X86::RSI), X86::RSP, false, 8);
        int i = 0;
        for(char c : rso.str()) {
            addRegOffset(BuildMI(InstSelMBB, InstSelMBB.end(), DebugLoc(), TII.get(X86::MOV8mi)), X86::RSI, false, i*sizeof(char)).addImm(c);
            i++;
        }
        // Add terminating NUL character
        addRegOffset(BuildMI(InstSelMBB, InstSelMBB.end(), DebugLoc(), TII.get(X86::MOV8mi)), X86::RSI, false, i*sizeof(char)).addImm(0);
#endif

        // XXX: Create the external symbol and get target flags (e.g, X86II::MO_PLT) for linking
        MachineOperand MO = MachineOperand::CreateES("selInst");
        MO.setTargetFlags( Subtarget.classifyGlobalFunctionReference( nullptr, *MF.getMMI().getModule() ) );
        BuildMI(InstSelMBB, InstSelMBB.end(), DebugLoc(), TII.get(X86::CALL64pcrel32)).addOperand( MO );

        // TEST for jump (see code later), XXX: THIS SETS FLAGS FOR THE JMP, be careful not to mess with them until the branch
        addDirectMem(BuildMI(InstSelMBB, InstSelMBB.end(), DebugLoc(), TII.get(X86::TEST8mi)), X86::RDI).addImm(0x1);

        emitDeallocateStack( InstSelMBB, InstSelMBB.end(), AlignedStackSize );
#ifdef INSTR_PRINT
        emitPopReg( InstSelMBB, InstSelMBB.end(), X86::RSI );
#endif
        // POP RDI
        emitPopReg( InstSelMBB, InstSelMBB.end(), X86::RDI );

        emitPopContextRegs( InstSelMBB, InstSelMBB.end() );

        SmallVector<MachineOperand, 1> Cond;
        Cond.push_back(MachineOperand::CreateImm(X86::COND_E));
        InstSelMBB.addSuccessor(&PostFIMBB);
        InstSelMBB.addSuccessor(&PreFIMBB);
        TII.InsertBranch(InstSelMBB, &PostFIMBB, &PreFIMBB, Cond, DebugLoc());
    }

    /* ============================================================= END OF InstSelMBB ========================================================== */

    /* ============================================================== CREATE PreFIMBB ============================================================== */

    // SystemV x64 calling conventions, args: RDI, RSI, RDX, RCX, R8, R9, XMM0-7, RTL

    emitPushContextRegs( PreFIMBB, PreFIMBB.end() );

    // PUSH RDI for doInject arg1 (unsigned, number of ops)
    emitPushReg( PreFIMBB, PreFIMBB.end(), X86::RDI );
    // PUSH RSI for doInject arg2 (uint64_t *, &op)
    emitPushReg( PreFIMBB, PreFIMBB.end(), X86::RSI );
    // PUSH RDX for doInject arg3 (uint64_t *, &size)
    emitPushReg( PreFIMBB, PreFIMBB.end(), X86::RDX );
    // PUSH RCX for doInject arg4 (uint64_t *, bitmask)
    emitPushReg( PreFIMBB, PreFIMBB.end(), X86::RCX );

    // The size and number of pointer arguments other than the bitmask
    unsigned PointerDataSize = 8;
    // SUB to create stack space for doInject arg2, arg3, arg4
    // TODO: Reduce stack space, ops, size array fit in uint16_t types
    // XXX: Align to 16-bytes
    int64_t size = (PointerDataSize + FIRegs.size() * PointerDataSize + MaxRegSize);
    int64_t AlignedStackSize = emitAllocateStackAlign16B( PreFIMBB, PreFIMBB.end(), size );
    // MOV RDI <= FIRegs.size(), doInject arg1 (uint64_t, number of ops)
    BuildMI(PreFIMBB, PreFIMBB.end(), DebugLoc(), TII.get(X86::MOV64ri), X86::RDI).addImm(FIRegs.size());
    // LEA RSI <= &op, doInject arg2 (uint64_t *, &op, 8B)
    addRegOffset(BuildMI(PreFIMBB, PreFIMBB.end(), DebugLoc(), TII.get(X86::LEA64r), X86::RSI), X86::RSP, false, MaxRegSize + PointerDataSize * FIRegs.size());
    // LEA RDX <= &size, doInject arg3 (uint64_t *, &size, number of ops * 8B)
    addRegOffset(BuildMI(PreFIMBB, PreFIMBB.end(), DebugLoc(), TII.get(X86::LEA64r), X86::RDX), X86::RSP, false, MaxRegSize);
    // MOV RDX <= RSP, doInject arg4 (uint8_t *, &bitmask, MaxRegSize B)
    addRegOffset(BuildMI(PreFIMBB, PreFIMBB.end(), DebugLoc(), TII.get(X86::LEA64r), X86::RCX), X86::RSP, false, 0);
    int64_t BitmaskStackOffset = StackOffset;
    // XXX: Beward of type casts, signed integers needed
    int64_t OpSelStackOffset = StackOffset + (int64_t)MaxRegSize + (int64_t)PointerDataSize * FIRegs.size();
    // Fill in size array
    for(unsigned i = 0; i < FIRegs.size(); i++) {
        unsigned FIReg = FIRegs[i];
        const TargetRegisterClass *TRC = TRI.getMinimalPhysRegClass(FIReg);
        // Size is in bytes
        unsigned RegSize = TRC->getSize();
        MaxRegSize = RegSize > MaxRegSize ? RegSize : MaxRegSize;
        addRegOffset(BuildMI(PreFIMBB, PreFIMBB.end(), DebugLoc(), TII.get(X86::MOV64mi32)), X86::RDX, false, i * PointerDataSize).addImm(RegSize);
    }

    //addDirectMem(BuildMI(PreFIMBB, PreFIMBB.end(), DebugLoc(), TII.get(X86::MOV64mi32)), X86::RDI).addImm(0x0);

    // XXX: Create the external symbol and get target flags (e.g, X86II::MO_PLT) for linking
    MachineOperand MO = MachineOperand::CreateES("doInject");
    MO.setTargetFlags( Subtarget.classifyGlobalFunctionReference( nullptr, *MF.getMMI().getModule() ) );
    BuildMI(PreFIMBB, PreFIMBB.end(), DebugLoc(), TII.get(X86::CALL64pcrel32)).addOperand( MO );

    // POP doInject arg2, arg3, ar4
    //addRegOffset(BuildMI(PreFIMBB, PreFIMBB.end(), DebugLoc(), TII.get(X86::LEA64r), X86::RSP), X86::RSP, false, AlignedStackSpace);
    emitDeallocateStack( PreFIMBB, PreFIMBB.end(), AlignedStackSize );
    // POP RCX
    emitPopReg( PreFIMBB, PreFIMBB.end(), X86::RCX );
    // POP RDX
    emitPopReg( PreFIMBB, PreFIMBB.end(), X86::RDX );
    // POP RSI
    emitPopReg( PreFIMBB, PreFIMBB.end(), X86::RSI );
    // POP RDI
    emitPopReg( PreFIMBB, PreFIMBB.end(), X86::RDI );

    emitPopContextRegs( PreFIMBB, PreFIMBB.end() );

    PreFIMBB.addSuccessor(OpSelMBBs.front()); 
    TII.InsertBranch(PreFIMBB, OpSelMBBs.front(), nullptr, None, DebugLoc());

    /* ============================================================= END OF PreFIMBB ============================================================= */

    /* ============================================================== CREATE OpSelMBBs =============================================================== */

    // Jump tables to selected op
    for(int OpIdx = FIRegs.size()-1, OpSelIdx = 0; OpIdx > 0; OpIdx--, OpSelIdx++) { //no need to jump to 0th operand, fall through
        MachineBasicBlock &OpSelMBB = *OpSelMBBs[OpSelIdx];
        MachineBasicBlock *NextOpSelMBB = OpSelMBBs[OpSelIdx+1];
        addRegOffset(BuildMI(OpSelMBB, OpSelMBB.end(), DebugLoc(), TII.get(X86::CMP64mi8)), X86::RSP, false, OpSelStackOffset).addImm(OpIdx);
        SmallVector<MachineOperand, 1> Cond;
        Cond.push_back(MachineOperand::CreateImm(X86::COND_E));
        OpSelMBB.addSuccessor(FIMBBs[OpIdx]);
        OpSelMBB.addSuccessor(NextOpSelMBB);
        TII.InsertBranch(OpSelMBB, FIMBBs[OpIdx], NextOpSelMBB, Cond, DebugLoc());
    }
    // Add the fall through OpSelMBB
    OpSelMBBs.back()->addSuccessor(FIMBBs[0]);
    TII.InsertBranch(*(OpSelMBBs.back()), FIMBBs[0], nullptr, None, DebugLoc());

    /* ============================================================== END OF OpSelMBBs =============================================================== */


    /* ============================================================== CREATE FIMBBs =============================================================== */
    for(unsigned idx = 0; idx < FIRegs.size(); idx++) {
        unsigned FIReg = FIRegs[idx];
        MachineBasicBlock &FIMBB = *FIMBBs[idx];

        const TargetRegisterClass *TRC = TRI.getMinimalPhysRegClass(FIReg);
        unsigned RegSize = TRC->getSize();
        unsigned RegSizeBits = RegSize * 8;

        // ProxyFIReg defaults to the register itself. It can be set to a different 
        // registers if FIReg = FLAGS | SP | RAX. FI operates on ProxyFIReg, and it 
        // is later copied to FIReg, if needed.
        unsigned ProxyFIReg = FIReg;

        // TODO: Test for 256-bit and 512-bit vector registers
        if(RegSizeBits <= 32) {
            // If it's one of the workhorse registers, used a different register as a proxy
            if(TRI.getSubRegIndex(X86::RSP, FIReg) || TRI.getSubRegIndex(X86::RBP, FIReg) || TRI.getSubRegIndex(X86::RAX, FIReg)) {
                ProxyFIReg = X86::RBX;

                unsigned RegStackOffset = 0;
                // Set the right offset in the stack
                if(TRI.getSubRegIndex(X86::RSP, FIReg))
                    RegStackOffset = RSPOffset;
                else if(TRI.getSubRegIndex(X86::RBP, FIReg))
                    RegStackOffset = RBPOffset;
                else if(TRI.getSubRegIndex(X86::RAX, FIReg))
                    RegStackOffset = RAXOffset;

                // PUSH Proxy to use for FI
                BuildMI(FIMBB, FIMBB.end(), DebugLoc(), TII.get(X86::PUSH64r)).addReg(ProxyFIReg);
                BitmaskStackOffset += 8;
                addRegOffset(BuildMI(FIMBB, FIMBB.end(), DebugLoc(), TII.get(X86::MOV64rm), ProxyFIReg), X86::RBP, false, RegStackOffset);
            }
            // RAX is already the proxy for EFLAGS 
            else if(FIReg == X86::EFLAGS)
                ProxyFIReg = X86::RAX;

            addRegOffset(BuildMI(FIMBB, FIMBB.end(), DebugLoc(), TII.get(X86::XOR32rm), ProxyFIReg).addReg(ProxyFIReg), X86::RSP, false, BitmaskStackOffset);

            if(TRI.getSubRegIndex(X86::RSP, FIReg) || TRI.getSubRegIndex(X86::RBP, FIReg) || TRI.getSubRegIndex(X86::RAX, FIReg)) {
                unsigned RegStackOffset = 0;
                // Set the right offset in the stack
                if(TRI.getSubRegIndex(X86::RSP, FIReg))
                    RegStackOffset = RSPOffset;
                else if(TRI.getSubRegIndex(X86::RBP, FIReg))
                    RegStackOffset = RBPOffset;
                else if(TRI.getSubRegIndex(X86::RAX, FIReg))
                    RegStackOffset = RAXOffset;

                // Store XOR result to stack
                addRegOffset(BuildMI(FIMBB, FIMBB.end(), DebugLoc(), TII.get(X86::MOV64mr)), X86::RBP, false, RegStackOffset).addReg(ProxyFIReg);
                // POP Proxy
                BuildMI(FIMBB, FIMBB.end(), DebugLoc(), TII.get(X86::POP64r)).addReg(ProxyFIReg);
            }
        }
        else if(RegSizeBits <= 64) {
            if(FIReg == X86::RSP || FIReg == X86::RBP || FIReg == X86::RAX) {
                ProxyFIReg = X86::RBX;

                unsigned RegStackOffset = 0;
                // Set the right offset in the stack
                if(FIReg == X86::RSP)
                    RegStackOffset = RSPOffset;
                else if(FIReg == X86::RBP)
                    RegStackOffset = RBPOffset;
                else if(FIReg == X86::RAX)
                    RegStackOffset = RAXOffset;

                // PUSH Proxy to use for FI
                BuildMI(FIMBB, FIMBB.end(), DebugLoc(), TII.get(X86::PUSH64r)).addReg(ProxyFIReg);
                BitmaskStackOffset += 8;
                addRegOffset(BuildMI(FIMBB, FIMBB.end(), DebugLoc(), TII.get(X86::MOV64rm), ProxyFIReg), X86::RBP, false, RegStackOffset);
            }

            addRegOffset(BuildMI(FIMBB, FIMBB.end(), DebugLoc(), TII.get(X86::XOR64rm), ProxyFIReg).addReg(ProxyFIReg), X86::RSP, false, BitmaskStackOffset);

            if(FIReg == X86::RSP || FIReg == X86::RBP || FIReg == X86::RAX) {
                unsigned RegStackOffset = 0;
                // Set the right offset in the stack
                if(FIReg == X86::RSP)
                    RegStackOffset = RSPOffset;
                else if(FIReg == X86::RBP)
                    RegStackOffset = RBPOffset;
                else if(FIReg == X86::RAX)
                    RegStackOffset = RAXOffset;

                // Store XOR result to stack
                addRegOffset(BuildMI(FIMBB, FIMBB.end(), DebugLoc(), TII.get(X86::MOV64mr)), X86::RBP, false, RegStackOffset).addReg(ProxyFIReg);
                // POP Proxy
                BuildMI(FIMBB, FIMBB.end(), DebugLoc(), TII.get(X86::POP64r)).addReg(ProxyFIReg);
            }
        }
        else if(RegSizeBits <= 128 || RegSizeBits <=256 || RegSizeBits <=512 ) {
            addRegOffset(BuildMI(FIMBB, FIMBB.end(), DebugLoc(), TII.get(X86::PXORrm), ProxyFIReg).addReg(ProxyFIReg), X86::RSP, false, BitmaskStackOffset);
        }
        else
            assert(false && "RegSizeBits is invalid!\n");

        FIMBB.addSuccessor(&PostFIMBB);
        TII.InsertBranch(FIMBB, &PostFIMBB, nullptr, None, DebugLoc());
    }

    /* ============================================================== END OF FIMBB =============================================================== */

    /* ============================================================ CREATE PostFIMBB ============================================================= */

    {
        emitRestoreFrameFlags( PostFIMBB, PostFIMBB.end() );
    }


    /* ============================================================ END OF PostFIMBB ============================================================= */

    assert(StackOffset == 0 && "StackOffset must be 0");
}

// code backup
#if 0
MachineInstr *MI = MO.getParent();
dbgs() << "another dump:"; MI->dump();
MachineBasicBlock::LivenessQueryResult LQR = MachineBasicBlock::LQR_Unknown;
MachineBasicBlock *MBB = MI->getParent();
MachineInstr &NextMI = *(++MI->getIterator());
dbgs() << "2. another dump:"; NextMI.dump();
LQR = MBB->computeRegisterLiveness(&TRI, X86::RAX, &NextMI);

dbgs() << "LQR: " << LQR << "\n";
//LQR = MachineBasicBlock::LQR_Live;
#endif

