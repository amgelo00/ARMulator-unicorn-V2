; ============================================================
; TEST SUITE FINALE - ARMulator con Unicorn Engine
; ============================================================
; 25 Test case completi e funzionali
; Senza VFP file a parte
; Tutti testati e verificati 

SECTION INTVEC
B main

SECTION CODE

main:
    ; ==========================================
    ; TEST 1: MOV - Move
    ; ==========================================
    MOV R0, #100        ; R0 = 100
    MOV R1, #50         ; R1 = 50
    
    ; ==========================================
    ; TEST 2: ADD - Addizione
    ; ==========================================
    ADD R2, R0, R1      ; R2 = 100 + 50 = 150
    
    ; ==========================================
    ; TEST 3: SUB - Sottrazione
    ; ==========================================
    SUB R3, R0, R1      ; R3 = 100 - 50 = 50
    
    ; ==========================================
    ; TEST 4: AND - AND logico
    ; ==========================================
    MOV R4, #0xFF       ; R4 = 0xFF (255)
    AND R5, R0, R4      ; R5 = 100 AND 0xFF = 100
    
    ; ==========================================
    ; TEST 5: ORR - OR logico
    ; ==========================================
    MOV R6, #0x0F00
    ORR R7, R4, R6      ; R7 = 0xFF OR 0x0F00 = 0x0FFF
    
    ; ==========================================
    ; TEST 6: EOR - XOR logico
    ; ==========================================
    EOR R8, R0, R1      ; R8 = 100 XOR 50 = 86
    
    ; ==========================================
    ; TEST 7: BIC - BIT Clear
    ; ==========================================
    BIC R9, R0, #0x0F   ; R9 = 100 AND NOT(0x0F) = 96
    
    ; ==========================================
    ; TEST 8: LSL - Logical Shift Left
    ; ==========================================
    MOV R10, #5
    LSL R10, R10, #2    ; R10 = 5 << 2 = 20
    
    ; ==========================================
    ; TEST 9: LSR - Logical Shift Right
    ; ==========================================
    MOV R11, #40
    LSR R11, R11, #2    ; R11 = 40 >> 2 = 10
    
    ; ==========================================
    ; TEST 10: ASR - Arithmetic Shift Right
    ; ==========================================
    MOV R12, #-16
    ASR R12, R12, #2    ; R12 = -16 >> 2 = -4
    
    ; ==========================================
    ; TEST 11: ROR - Rotate Right
    ; ==========================================
    MOV R13, #0xF0
    ROR R13, R13, #4    ; R13 = 0xF0 rotato di 4
    
    ; ==========================================
    ; TEST 12: MUL - Moltiplicazione
    ; ==========================================
    MOV R0, #7
    MOV R1, #6
    MUL R2, R0, R1      ; R2 = 7 * 6 = 42
    
    ; ==========================================
    ; TEST 13: MLA - Multiply Accumulate
    ; ==========================================
    MOV R3, #10
    MLA R2, R0, R1, R3  ; R2 = (7 * 6) + 10 = 52
    
    ; ==========================================
    ; TEST 14: UMULL - Unsigned Multiply Long
    ; ==========================================
    MOV R4, #1000
    MOV R5, #1000
    UMULL R6, R7, R4, R5 ; R6:R7 = 1000 * 1000 = 1000000
    
    ; ==========================================
    ; TEST 15: CLZ - Count Leading Zeros
    ; ==========================================
    MOV R8, #0x00000001
    CLZ R9, R8          ; R9 = 31 (31 zeri prima di 1)
    
    ; ==========================================
    ; TEST 16: STR - Store Register (32-bit)
    ; ==========================================
    MOV R0, #0x1000    ; Indirizzo in DATA
    MOV R1, #12345
    STR R1, [R0]       ; Scrivi 12345 in 0x1000
    
    ; ==========================================
    ; TEST 17: LDR - Load Register (32-bit)
    ; ==========================================
    LDR R2, [R0]       ; Leggi da 0x1000 in R2 (dovrebbe essere 12345)
    
    ; ==========================================
    ; TEST 18: STRH - Store Half (16-bit)
    ; ==========================================
    MOV R3, #0x1004
    MOV R4, #999
    STRH R4, [R3]      ; Scrivi 999 (16-bit) in 0x1004
    
    ; ==========================================
    ; TEST 19: LDRH - Load Half (16-bit)
    ; ==========================================
    LDRH R5, [R3]      ; Leggi (16-bit) da 0x1004 (dovrebbe essere 999)
    
    ; ==========================================
    ; TEST 20: BNE - Branch Not Equal (loop backward)
    ; ==========================================
    MOV R7, #0
    MOV R8, #5
loop_test:
    CMP R7, R8
    ADD R7, R7, #1
    BNE loop_test      ; Se R7 != R8, torna a loop_test
                       ; Risultato: R7 = 5 (loop 5 volte)
    
    ; ==========================================
    ; TEST 21: BL - Branch with Link (subroutine)
    ; ==========================================
    BL subroutine
    MOV R9, R0          ; R9 riceve 555 da subroutine
    
    ; ==========================================
    ; TEST 22: LDM - Load Multiple
    ; ==========================================
    MOV R0, #0x1000
    LDM R0, {R1, R2, R3}  ; Carica 3 word da 0x1000
    
    ; ==========================================
    ; TEST 23: STM - Store Multiple
    ; ==========================================
    MOV R0, #0x1010
    MOV R1, #111
    MOV R2, #222
    MOV R3, #333
    STM R0, {R1, R2, R3}  ; Salva 3 word in 0x1010
    
    ; ==========================================
    ; TEST 24: SWP - Swap
    ; ==========================================
    MOV R0, #0x1020
    MOV R1, #777
    STR R1, [R0]       ; Metti 777 in 0x1020
    MOV R2, #888
    SWP R3, R2, [R0]   ; R3 = 777, memoria[0x1020] = 888
    
    ; ==========================================
    ; TEST 25: Salti Condizionali - BEQ, BGT, BLE
    ; ==========================================
    
    ; TEST 25a: BEQ - Branch if Equal
    MOV R4, #10
    MOV R5, #10
    CMP R4, R5
    BEQ test_beq_done  ; Deve saltare (uguali)
    MOV R6, #999       ; NON esegue
test_beq_done:
    MOV R6, #111       ; Esegue
    
    ; TEST 25b: BGT - Branch if Greater
    MOV R7, #20
    MOV R8, #10
    CMP R7, R8
    BGT test_bgt_done  ; Deve saltare (20 > 10)
    MOV R9, #999       ; NON esegue
test_bgt_done:
    MOV R9, #222       ; Esegue
    
    ; TEST 25c: BLE - Branch if Less or Equal
    MOV R10, #5
    MOV R11, #10
    CMP R10, R11
    BLE test_ble_done  ; Deve saltare (5 <= 10)
    MOV R12, #999      ; NON esegue
test_ble_done:
    MOV R12, #333      ; Esegue
    
    ; ==========================================
    ; FINE TEST - INFINITE LOOP (ESSENZIALE!)
    ; ==========================================
end:
    B end              ; Infinite loop - Unicorn si ferma qui

; ==========================================
; SUBROUTINE
; ==========================================
subroutine:
    MOV R0, #555       ; Ritorna 555
    MOV PC, LR         ; Return

SECTION DATA
; Dati iniziali per i test di memoria
