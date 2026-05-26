SECTION INTVEC

B main

SECTION CODE

main
    MOV R0, #100
    MOV R1, #200
    MUL R2, R0, R1
    UMULL R3, R4, R0, R1
    MOV R5, #0x1000
    MOV R6, #0xABCD
    STRH R6, [R5]
    LDRH R7, [R5]
    CLZ R8, R0
    B .
B end

SECTION DATA
