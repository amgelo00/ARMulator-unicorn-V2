
from unicorn import *
from unicorn.arm_const import *
from components import Registers, Memory, Breakpoint, ComponentException
from history import History
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM
#è il file Test_integrazione_reg.py ma gestito con una classe efunzioni

class UnicornEmulator:
    
    def dichiarazione_var(self):
        """
            dichiarazione delle variabbili in un valore nullo per evitare errori
        """
        self.mu = None
        self.bytecode = None
        self.errors = None

        self.history = None
        self.Reg = None
        self.mem = None

        self.INTVEC_ADDR = None
        self.CODE_ADDR = None
        self.DATA_ADDR = None

    def enable_vfp(uc):#non va s
        # Enable CP10 and CP11 in CPACR
        cpacr = uc.reg_read(UC_ARM_REG_C1_C0_2)
        cpacr |= (0xF << 20)  # Set bits 20-23
        uc.reg_write(UC_ARM_REG_C1_C0_2, cpacr)
    
        # Set the EN bit in FPEXC to enable VFP system
        fpexc = 0x40000000
        uc.reg_write(UC_ARM_REG_FPEXC, fpexc)

    def setup(self):
        
        self.mu = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        self.ks = Ks(KS_ARCH_ARM, KS_MODE_ARM)
    
   
        self.history = History()
        self.Reg = Registers(self.history)
        self.mem = Memory(self.history, self.bytecode)
        self.history.clear()
        self.csprinizale = self.Reg.CPSR
    
   
        self.mappatura_mem()
    
    
        self.sincronizzazione_iniziale()
        
    def mappatura_mem(self):
       
        
    
    
        #mappatura memoria,fatta tramite i dati della classe Memory, che contiene i dati di INTVEC, CODE e DATA, con i rispettivi indirizzi
        self.INTVEC_ADDR = self.bytecode["__MEMINFOSTART"]["INTVEC"]
        self.CODE_ADDR   = self.bytecode["__MEMINFOSTART"]["CODE"]
        self.DATA_ADDR   = self.bytecode["__MEMINFOSTART"]["DATA"]
        #creazione dell'istanza di Unicorn per ARM in modalità ARM (non Thumb), mappatura della memoria, e scrittura dei dati di INTVEC, CODE e DATA nei rispettivi indirizzi di memoria. Questo permette a Unicorn di eseguire il codice e gestire gli interrupt correttamente durante la simulazione.
        self.mu.mem_map(0x0, 0x10000)
        #self.mu.reg_write(UC_ARM_REG_CPSR, cpsr)
        self.mu.reg_write(UC_ARM_REG_FPSCR, 0x00000000)
        #HOk unicorn per brekpoint 
        self.mu.hook_add(UC_HOOK_CODE, self.hook_code)#hook per i breakpoint, che ferma l'esecuzione quando si raggiunge un indirizzo di breakpoint, o quando si accede in lettura/scrittura a un indirizzo di breakpoint, a seconda del tipo di breakpoint impostato. Questo permette di eseguire il debug del codice e analizzare il comportamento del programma durante la simulazione.
        self.mu.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE, self.hook_mem)#  hook per i breakpoint di memoria, che ferma l'esecuzione quando si accede in lettura/scrittura a un indirizzo di breakpoint, a seconda del tipo di breakpoint impostato. Questo permette di eseguire il debug del codice e analizzare il comportamento del programma durante la simulazione.
        self.mu.mem_write(self.INTVEC_ADDR, bytes(self.mem.data["INTVEC"]))
        self.mu.mem_write(self.CODE_ADDR,   bytes(self.mem.data["CODE"]))
        self.mu.mem_write(self.DATA_ADDR,   bytes(self.mem.data["DATA"]))
        # print degli indirizzi di memoria, per verificare che siano corretti, e per avere un riferimento durante la simulazione da toglirere dopo
        #print("INTVEC_ADDR", self.INTVEC_ADDR)
        #print("CODE_ADDR", self.CODE_ADDR)
        #   print("DATA_ADDR", self.DATA_ADDR)
        # Abilita VFP/NEON
        try:
           from unicorn.arm_const import UC_ARM_REG_FPEXC
           self.mu.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
           cpsr = self.mu.reg_read(UC_ARM_REG_CPSR)
           cpsr |= (0xF << 20)
           self.mu.reg_write(UC_ARM_REG_CPSR, cpsr)
           print("VFP enabled")
        except Exception as e:
           print(f"VFP not available: {e}")

    def sincronizzazione_iniziale(self):
        #sicronizzazione inizilae dei registri, in modo da poterli stampare alla fine, e anche per poterli usare durante la simulazione,
        #ad esempio per le istruzioni che modificano i registri, o per le istruzioni di salto che usano i registri come indirizzi
        # Sincronizzazione iniziale da components a Unicorn
        print("\n--- Sincronizzazione iniziale ---")
        # R0-R14
        for i in range(15):
            self.mu.reg_write(UC_ARM_REG_R0 + i,
                              self.Reg.getRegister(self.Reg.mode, i))
        # PC (senza +8 perché Unicorn usa PC reale)
        self.mu.reg_write(UC_ARM_REG_PC, self.CODE_ADDR)  
        # CPSR
        self.mu.reg_write(UC_ARM_REG_CPSR, self.csprinizale)  # usiamo il valore iniziale del CPSR salvato durante il setup
        # SPSR solo se non User mode
        if self.Reg.mode != "User":
            self.mu.reg_write(UC_ARM_REG_SPSR, self.Reg.SPSR)

        print("Sincronizzazione iniziale completata!")
        for i in range(15):
            val = self.mu.reg_read(UC_ARM_REG_R0 + i)
            print(f"R{i} = {val}")
        print(f"PC = {self.mu.reg_read(UC_ARM_REG_PC)}")
        print(f"CPSR = {self.mu.reg_read(UC_ARM_REG_CPSR)}")
        if self.Reg.mode != "User":
            print(f"SPSR = {self.mu.reg_read(UC_ARM_REG_SPSR)}")
        
    def run(self):
        try:
            self.mu.emu_start(
                self.CODE_ADDR,
                self.CODE_ADDR + len(bytes(self.mem.data["CODE"])),
                count=1000
            )
        except Exception as e:
            print(f"Errore durante l'esecuzione: {e}")
        self.history.newCycle()#aggiungiamo un ciclo alla history, per segnare la fine dell'esecuzione, e poter stampare le modifiche alla fine della simulazione
    def verifica(self):
        #verifica e stampa dei risultati
        print("\n--- Verifica sincronizzazione ---")

       

        for i in range(15):
            self.Reg.setRegister(
                self.Reg.mode,
                i,
                self.mu.reg_read(UC_ARM_REG_R0 + i)
            )

        self.Reg.setRegister(
            self.Reg.mode,
            15,
            self.mu.reg_read(UC_ARM_REG_PC)+8
        )

        self.Reg.CPSR = self.mu.reg_read(UC_ARM_REG_CPSR)

        if self.Reg.mode != "User":
            self.Reg.SPSR = self.mu.reg_read(UC_ARM_REG_SPSR)

        # confronto
        sync_ok = True

        for i in range(15):
            val_unicorn = self.mu.reg_read(UC_ARM_REG_R0 + i)
            val_component = self.Reg.getRegister(self.Reg.mode, i)

            if val_unicorn != val_component:
                print(f"R{i} NON sincronizzato! Unicorn={val_unicorn} Component={val_component}")
                sync_ok = False
            else:
                print(f"R{i} OK = {val_unicorn}")

        # PC
        val_unicorn_pc = self.mu.reg_read(UC_ARM_REG_PC) + 8
        val_component_pc = self.Reg.getRegister(self.Reg.mode, 15)

        if val_unicorn_pc != val_component_pc:
            print(f"PC NON sincronizzato! Unicorn={val_unicorn_pc} Component={val_component_pc}")
            sync_ok = False
        else:
            print(f"PC OK = {val_unicorn_pc}")

        # CPSR
        val_unicorn_cpsr = self.mu.reg_read(UC_ARM_REG_CPSR)

        if val_unicorn_cpsr != self.Reg.CPSR:
            print(f"CPSR NON sincronizzato! Unicorn={val_unicorn_cpsr} Component={self.Reg.CPSR}")
            sync_ok = False
        else:
            print(f"CPSR OK = {val_unicorn_cpsr}")

        # risultato
        if sync_ok:
            #print("\n Sincronizzazione completata correttamente!")
            pass
        else:
            #print("\n Errore di sincronizzazione!")
            pass
        #memoria: confrontiamo byte per byte la memoria di Unicorn con quella della componente Memory, e segnaliamo alla history eventuali differenze. Questo permette di tenere traccia di tutte le modifiche alla memoria durante la simulazione, e di poterle stampare alla fine o durante il debug.
        for sec, data in self.mem.data.items():
            base = self.mem.startAddr[sec]
            for offset in range(len(data)):
                new_byte = self.mu.mem_read(base + offset, 1)[0]
                old_byte = self.mem.data[sec][offset]
                if new_byte != old_byte:
                    self.mem.data[sec][offset] = new_byte
    def stampa_history(self):
        print("\n--- History ---")
        for cycle_idx, cycle in enumerate(self.history.history):
            print(f"\nCiclo {cycle_idx}:")
            for classe, cambiamenti in cycle.items():
                if cambiamenti:
                    print(f"  {classe.__name__}:")
                    for chiave, (old, new) in cambiamenti.items():
                        print(f"    {chiave}: {old} → {new}")    
    def reset(self):
        # 1. PuliscE history
        self.history.clear()
        self.mem.data = {k: bytearray(v) for k, v in self.mem.initdata.items()}#reset della memoria della componente, per allinearla a quella di Unicorn
        # Ricarica memoria in Unicorn
        self.mu.mem_write(self.INTVEC_ADDR, bytes(self.mem.data["INTVEC"]))
        self.mu.mem_write(self.CODE_ADDR,   bytes(self.mem.data["CODE"]))
        self.mu.mem_write(self.DATA_ADDR,   bytes(self.mem.data["DATA"]))
    
        # 3. Azzera registri in Unicorn
        for i in range(15):
            self.mu.reg_write(UC_ARM_REG_R0 + i, 0)
        #reg uso spec
        self.mu.reg_write(UC_ARM_REG_PC, self.CODE_ADDR)  
        self.mu.reg_write(UC_ARM_REG_CPSR, self.csprinizale)
        #per i rest del pc e cspr
        self.Reg.setRegister(self.Reg.mode, 15, self.CODE_ADDR+8 , logToHistory=False)#PC in Unicorn è sempre +8 rispetto al valore reale
        
        if self.Reg.mode != "User":
            self.mu.reg_write(UC_ARM_REG_SPSR, self.Reg.SPSR)
            
        # 4. Azzera registri in componente, senza loggare in history
        for i in range(15):
            self.Reg.setRegister(self.Reg.mode, i, 0, logToHistory=False)
        self.Reg.setRegister(self.Reg.mode, 15, self.CODE_ADDR + 8, logToHistory=False)
        self.Reg.CPSR = self.csprinizale
        #print("\n--- Reset completato ---")
    def load_asm_from_string(self, asm_code):
        """Carica codice ARM direttamente da stringa"""
        try:
            encoding, count = self.ks.asm(asm_code)
            bytecode_assembled = bytes(encoding)
        
            self.mu.mem_write(self.CODE_ADDR, bytecode_assembled)
            #print(f"✅ Assemblato: {count} istruzioni ({len(bytecode_assembled)} bytes)")
        
            self.mu.reg_write(UC_ARM_REG_PC, self.CODE_ADDR)
            return bytecode_assembled
        except Exception as e:
            print(f"Errore Keystone: {e}")
            return None
    # Hook per i breakpoint, che ferma l'esecuzione quando si raggiunge un indirizzo di breakpoint, o quando si accede in lettura/scrittura a un indirizzo di breakpoint, a seconda del tipo di breakpoint impostato. Questo permette di eseguire il debug del codice e analizzare il comportamento del programma durante la simulazione.
    def hook_code(self, mu, addr, size, _):
        if addr in self.mem.breakpoints:
            if self.mem.breakpoints[addr] & 1:
                mu.emu_stop()
    # Hook per i breakpoint di memoria, che ferma l'esecuzione quando si accede in lettura/scrittura a un indirizzo di breakpoint, a seconda del tipo di breakpoint impostato. Questo permette di eseguire il debug del codice e analizzare il comportamento del programma durante la simulazione.
    def hook_mem(self, mu, access, addr, size, value, _):
        if addr in self.mem.breakpoints:
            if access == UC_MEM_READ and self.mem.breakpoints[addr] & 4:
                mu.emu_stop()
            if access == UC_MEM_WRITE and self.mem.breakpoints[addr] & 2:
                mu.emu_stop()

    def step(self, sim):
        # sync components → Unicorn
        for i in range(15):
            self.mu.reg_write(UC_ARM_REG_R0 + i, sim.regs.banks["User"][i].val)
        pc_real = sim.regs.banks["User"][15].val - sim.pcoffset
        self.mu.reg_write(UC_ARM_REG_PC, pc_real)
        self.mu.reg_write(UC_ARM_REG_CPSR, sim.regs.CPSR)
        #snyc memoria per rislre il proma dell off del pc 
        self.mu.mem_write(self.INTVEC_ADDR, bytes(self.mem.data["INTVEC"]))
        self.mu.mem_write(self.CODE_ADDR,   bytes(self.mem.data["CODE"]))
        self.mu.mem_write(self.DATA_ADDR,   bytes(self.mem.data["DATA"]))
        #  ABILITA VFP PRIMA DI ESEGUIRE
        cpsr = sim.regs.CPSR | 0x00C00000  # Abilita CP10 e CP11
        self.mu.reg_write(UC_ARM_REG_CPSR, cpsr)
        self.mu.reg_write(UC_ARM_REG_FPSCR, 0)
        for sec, data in sim.mem.data.items():
            base = sim.mem.startAddr[sec]
            if data:
                self.mu.mem_write(base, bytes(data))
        pc_before = self.mu.reg_read(UC_ARM_REG_PC)
        instr_bytes = self.mu.mem_read(pc_before, 4)
        #print(f"🎯 ESEGUO: PC=0x{pc_before:04x}, bytecode={instr_bytes.hex()}")
        # esegui 1 istruzione
        try:
            self.mu.emu_start(pc_real, 0, count=1)
            pc_after = self.mu.reg_read(UC_ARM_REG_PC)
            #print(f"🎯 PC DOPO emu_start: 0x{pc_after:04x}")

            # Sincronizza PC
            sim.regs.setRegister("User", 15, self.mu.reg_read(UC_ARM_REG_PC) + sim.pcoffset)
            new_pc_read = self.mu.reg_read(UC_ARM_REG_PC)
            #print(f"🎯 PC LETTO DA UNICORN: 0x{new_pc_read:04x}")
        except Exception as e:
            print(f"Errore durante l'esecuzione: {e}")
            #from simulatorOps.abstractOp import ExecutionException
            #raise ExecutionException(str(e))

            # sync Unicorn → components
        
        for i in range(15):
            new_val = self.mu.reg_read(UC_ARM_REG_R0 + i)
            sim.regs.setRegister("User", i, new_val)
        sim.regs.setRegister("User", 15, self.mu.reg_read(UC_ARM_REG_PC) + sim.pcoffset)
        sim.regs.CPSR = self.mu.reg_read(UC_ARM_REG_CPSR)

        # sync memoria
        for sec, data in sim.mem.data.items():
            base = sim.mem.startAddr[sec]
            for offset in range(len(data)):
                new_byte = self.mu.mem_read(base + offset, 1)[0]
                old_byte = sim.mem.data[sec][offset]
                if new_byte != old_byte:
                    sim.history.signalChange(sim.mem, {(sec, offset): (old_byte, new_byte)})
                    sim.mem.data[sec][offset] = new_byte

        # pcmodified
        new_pc = self.mu.reg_read(UC_ARM_REG_PC)
        sim.currentInstr.pcmodified = (new_pc != pc_real + 4)
    
        #print(f"🦄 step: PC={hex(pc_real)} → R0={sim.regs.banks['User'][0].val}")
    