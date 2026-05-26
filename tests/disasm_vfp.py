#!/usr/bin/env python3
"""Disassembla bytecode con Capstone"""

from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM

bytecode = bytes.fromhex("0100a0e30210a0e3100a00ee901a00ee201a30eefeffffea")

cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
cs.detail = True

print("📖 Disassembly:")
for instr in cs.disasm(bytecode, 0x80):
    print(f"  {hex(instr.address)}: {instr.mnemonic} {instr.op_str}")
