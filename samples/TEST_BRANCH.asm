SECTION INTVEC
B main

SECTION CODE
main:
    MOV R0, #0          ; R0 = contatore
    MOV R1, #10         ; R1 = limite

loop:
    ADD R0, R0, #1      ; R0 incrementa
    CMP R0, R1          ; confronta R0 con R1
    BNE loop            ; se diversi, torna a loop (SALTO BACKWARD!)
    
    MOV R2, #100        ; R2 = 100 (eseguito solo dopo loop)
    MOV R3, #200        ; R3 = 200
    MUL R4, R2, R3      ; R4 = R2 * R3 = 20000
    
    CLZ R5, R2          ; R5 = count leading zeros di 100

end:
    B end               ; loop infinito finale

SECTION DATA
