"""
assembler.py con Keystone Engine - VERSIONE CORRETTA FINALE
Mantiene la struttura bytecode del vecchio assembler
Gestisce salti forward con Keystone e salti backward manualmente

FIX APPLICATE:
  - FASE 1: addr= passato a Keystone per calcoli label corretti
  - FASE 2: Solo B, BL, BLX backward → manual
  - FASE 2: BNE, BEQ, BGT, BLE, ecc. → SEMPRE Keystone
"""

import struct
import re
from collections import defaultdict
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM
from settings import getSetting
from stateManager import StateManager

appState = StateManager()

memory_configs = {
    "simulation": {"INTVEC": 0x00, "CODE": 0x80, "DATA": 0x1000},
    "test": {"INTVEC": 0x100000, "CODE": 0x100080, "DATA": 0x101000},
}


def assemble_branch_manual(instr_type, target_addr, current_addr):
    """
    Assembla manualmente un salto ARM senza usare Keystone.
    Questo risolve il bug di Keystone con salti backward su Windows.
    NOTA: Solo per B, BL, BLX (non per i condizionali!)
    """
    offset = (target_addr - current_addr - 8) // 4
    offset = offset & 0xFFFFFF
    
    opcodes = {
        'B': 0x5,
        'BL': 0x5,
        'BLX': 0x4,
    }
    
    opcode = opcodes.get(instr_type, 0x5)
    bytecode = (0xE << 28) | (opcode << 25) | (offset & 0xFFFFFF)
    
    return struct.pack('<I', bytecode)


def parse(code, memLayout="simulation"):
    """
    Parse ARM assembly con Keystone Engine.
    Ritorna la stessa struttura bytecode del vecchio assembler.
    """
    
    # =========================================================================
    # AUTO-COMPLETAMENTO ROBUSTO
    # =========================================================================
    code_str = "\n".join(code) if isinstance(code, list) else code
    
    has_b_end = "B end" in code_str
    has_end_label = bool(re.search(r'^\s*end\s*:\s*$', code_str, re.MULTILINE))
    
    if has_b_end and not has_end_label:
        print(" Auto-completamento: aggiunto label 'end:' con 'B end'")
        code = code.split('\n') if isinstance(code, str) else list(code)
        
        data_idx = None
        for i, line in enumerate(code):
            if re.match(r'^\s*SECTION\s+DATA\s*$', line, re.IGNORECASE):
                data_idx = i
                break
        
        if data_idx is not None:
            code.insert(data_idx, "end:")
            code.insert(data_idx + 1, "    B end")
            code.insert(data_idx + 2, "")
        else:
            code.append("")
            code.append("end:")
            code.append("    B end")
    
    ks = Ks(KS_ARCH_ARM, KS_MODE_ARM)
    listErrors = []
    pcoffset = 8 if getSetting("PCbehavior") == "+8" else 0
    
    addrToLine = defaultdict(list)
    lineToAddr = {}
    assertions = defaultdict(list)
    snippetMode = False
    labelsAddr = {}
    
    bytecode = {
        "__MEMINFOSTART": {"SNIPPET_DUMMY_SECTION": 0},
        "__MEMINFOEND": {"SNIPPET_DUMMY_SECTION": 0},
    }
    
    maxAddrBySection = memory_configs[memLayout].copy()
    
    # Raccogli linee per sezione
    lines_by_section = {"INTVEC": [], "CODE": [], "DATA": []}
    current_section = None
    
    for line_idx, raw_line in enumerate(code):
        line = raw_line.strip()
        
        if ";" in line:
            line = line[:line.find(";")].strip()
        
        if not line:
            continue
        
        section_match = raw_line.strip().upper().startswith("SECTION")
        if section_match:
            match = re.match(r"SECTION\s+(\w+)", line, re.IGNORECASE)
            if match:
                current_section = match.group(1).upper()
                if current_section not in lines_by_section:
                    lines_by_section[current_section] = []
                continue
        
        if current_section:
            lines_by_section[current_section].append((line_idx, line))
    
    # =========================================================================
    # FASE 1: Trova TUTTI i label e calcola indirizzi
    # FIX: Passa addr= a Keystone per calcoli corretti
    # =========================================================================
    
    labels = {}
    current_addr = {}
    
    for section in ["INTVEC", "CODE", "DATA"]:
        current_addr[section] = maxAddrBySection[section]
    
    for section in ["INTVEC", "CODE", "DATA"]:
        for line_idx, line in lines_by_section[section]:
            # Label
            label_match = re.match(r"^(\w+):", line)
            if label_match:
                label_name = label_match.group(1)
                labels[label_name] = current_addr[section]
                continue
            
            # Istruzione
            if not line.strip():
                continue
            
            try:
                # FIX: Passa addr= così Keystone sa dove sta assemblando
                encoding, _ = ks.asm(line, addr=current_addr[section])
                if encoding:
                    current_addr[section] += len(bytes(encoding))
            except:
                # Fallback: ipotizza 4 byte
                current_addr[section] += 4
    
    # =========================================================================
    # FASE 2: Assembla risolvendo label con salti CORRETTI
    # =========================================================================
    
    for section in ["INTVEC", "CODE", "DATA"]:
        bytecode[section] = bytearray()
        current_addr[section] = maxAddrBySection[section]

    for section in ["INTVEC", "CODE", "DATA"]:
        for line_idx, line in lines_by_section[section]:
            # Skip label
            if re.match(r"^(\w+):", line):
                continue
        
            if not line.strip():
                continue
        
            instr_addr = current_addr[section]
            modified_line = line
            bytecode_bytes = None
            
            #  FIX: Solo B, BL, BLX backward → manual
            # BNE, BEQ, BGT, BLE, ecc. → SEMPRE Keystone
            if re.search(r'\b(B|BL|BLX)\s+', line):
                match = re.search(r'(B|BL|BLX)\s+(\w+|0x[0-9a-fA-F]+)', line)
                if match:
                    instr_type = match.group(1)
                    target_str = match.group(2)
                
                    # Risolvi target
                    if target_str in labels:
                        target_addr = labels[target_str]
                    else:
                        try:
                            target_addr = int(target_str, 0)
                        except:
                            target_addr = None
                
                    if target_addr is not None:
                        # SE È SALTO BACKWARD → ASSEMBLA MANUALMENTE
                        if target_addr < instr_addr:
                            bytecode_bytes = assemble_branch_manual(instr_type, target_addr, instr_addr)
                        else:
                            # SE È SALTO FORWARD → USA KEYSTONE
                            modified_line = f"{instr_type} 0x{target_addr:x}"
            
            # Se non è un salto manuale, usa Keystone
            if bytecode_bytes is None:
                # Sostituisci label con indirizzi (per istruzioni non-salto)
                if not re.search(r'\b(B|BL|BLX)\s+', line):
                    for label_name, label_addr in labels.items():
                        modified_line = re.sub(
                            r'\b' + re.escape(label_name) + r'\b',
                            str(label_addr),
                            modified_line
                        )
                
                # Assembla con Keystone
                try:
                    encoding, count = ks.asm(modified_line, addr=instr_addr)
                    
                    if encoding:
                        bytecode_bytes = bytes(encoding)
                
                except Exception as e:
                    print(f"Errore assemblaggio: {line} → {e}")
            
            # Aggiungi al bytecode della sezione
            if bytecode_bytes:
                bytecode[section].extend(bytecode_bytes)
                
                addrToLine[instr_addr].append(line_idx)
                
                if line_idx not in lineToAddr:
                    lineToAddr[line_idx] = []
                lineToAddr[line_idx].append(instr_addr)
                
                current_addr[section] += len(bytecode_bytes)
    
    # =========================================================================
    # Finalizza bytecode
    # =========================================================================
    
    bytecode["__MEMINFOSTART"] = {
        "INTVEC": maxAddrBySection["INTVEC"],
        "CODE": maxAddrBySection["CODE"],
        "DATA": maxAddrBySection["DATA"],
    }
    
    bytecode["__MEMINFOEND"] = {
        "INTVEC": maxAddrBySection["INTVEC"] + len(bytecode["INTVEC"]),
        "CODE": maxAddrBySection["CODE"] + len(bytecode["CODE"]),
        "DATA": maxAddrBySection["DATA"] + len(bytecode["DATA"]),
    }
    
    # Converti bytearray a bytes
    for section in ["INTVEC", "CODE", "DATA"]:
        if isinstance(bytecode[section], bytearray):
            bytecode[section] = bytes(bytecode[section])
    
    return bytecode, addrToLine, lineToAddr, assertions, snippetMode, []