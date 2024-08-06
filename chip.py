import os
import sys
import time
import pygame
from pygame import HWSURFACE, DOUBLEBUF
import math
import random


MEMORY      = [0] * 4096
I           = 0x0
V           = [0] * 16
PC          = 0x200
STACK       = [0] * 16
STACK_PTR   = 0
DELAY_TIMER = 0
SOUND_TIMER = 0
DISPLAY     = [0] * (64 * 32)
# load at addr 0x50
FONTSET = [
      0xF0, 0x90, 0x90, 0x90, 0xF0, # 0
	  0x20, 0x60, 0x20, 0x20, 0x70, # 1
	  0xF0, 0x10, 0xF0, 0x80, 0xF0, # 2
	  0xF0, 0x10, 0xF0, 0x10, 0xF0, # 3
	  0x90, 0x90, 0xF0, 0x10, 0x10, # 4
	  0xF0, 0x80, 0xF0, 0x10, 0xF0, # 5
	  0xF0, 0x80, 0xF0, 0x90, 0xF0, # 6
	  0xF0, 0x10, 0x20, 0x40, 0x40, # 7
	  0xF0, 0x90, 0xF0, 0x90, 0xF0, # 8
	  0xF0, 0x90, 0xF0, 0x10, 0xF0, # 9
	  0xF0, 0x90, 0xF0, 0x90, 0x90, # A
	  0xE0, 0x90, 0xE0, 0x90, 0xE0, # B
	  0xF0, 0x80, 0x80, 0x80, 0xF0, # C
	  0xE0, 0x90, 0x90, 0x90, 0xE0, # D
	  0xF0, 0x80, 0xF0, 0x80, 0xF0, # E
	  0xF0, 0x80, 0xF0, 0x80, 0x80  # F
]



def loadrom(file):
    """returns a list with bytes"""
    list = []
    size = os.path.getsize(file)
    with open(file, 'rb') as f:
        for _ in range(size):
            byte = f.read(1).hex()
            if byte != '':
                list.append(int(byte, base=16))   
        return list 


  
def cpu():
    """fetch-decode-execute cycle"""
    global PC
    global DISPLAY
    global SOUND_TIMER
    global DELAY_TIMER
    global STACK
    global STACK_PTR
    global MEMORY
    global I
    global V
    global FONTSET
          
    # opcode = byte + byte sucessor e.g. 22 + fc = 22fc opcode
    #time.sleep(0.03)
    opcode = (MEMORY[PC] << 8) | (MEMORY[PC + 1])
    hex_opcode = (hex(opcode))
    PC += 2 
    match (opcode & 0xF000): # first nibble
        case 0x0000:
            match (opcode & 0x00FF):
                case 0x00E0: # clear display
                   DISPLAY = [0] * (64 * 32)
                   print(f'{hex_opcode } CLS DISPLAY')
                case 0x00EE: # return from a subroutine
                    PC = STACK[STACK_PTR] 
                    STACK_PTR = STACK_PTR - 1    
                    print(f'{hex_opcode} RET PC = {hex(STACK[STACK_PTR])}')

    
        case 0x1000: # 1nnn
            nnn = (opcode & 0x0FFF )
            PC = nnn # - 2
            print(f'{hex_opcode} JMP {hex(nnn)} ')
            
           

        case 0x2000: # 2nnn
            nnn = opcode & 0x0FFF
            STACK_PTR = STACK_PTR + 1
            STACK[STACK_PTR] = PC
            PC = nnn
            print(f'{hex_opcode} CALL {hex(nnn)}')

        case 0x3000: # 3xkk
            x = (opcode & 0x0F00) >> 8
            kk = opcode & 0x00FF
            if V[x] == kk:
                PC += 2 
                print(f'{hex_opcode} SE {V[x]} {kk} (SKIPPING)')
            else:
                print(f'{hex_opcode} SE {V[x]} {kk} (NOT SKIPPING)')

        case 0x4000:
            x = (opcode & 0x0F00) >> 8
            kk = opcode & 0x00FF
            if V[x] != kk:
                PC += 2
                print(f'{hex_opcode} SNE {V[x]} {kk} (SKIPPING)')
            else:    
                print(f'{hex_opcode} SNE {V[x]} {kk} (NOT SKIPPING)')
        case 0x5000:
            x = (opcode & 0x0F00) >> 8
            y = (opcode & 0x00F0) >> 4
            if V[x] == V[y]:
                PC += 2
                print(f'{hex_opcode} SE {V[x]} {V[y]} (SKIPPING)')
            else:
                print(f'{hex_opcode} SE {V[x]} {V[y]} (NOT SKIPPING)')

           
        case 0x6000: # 6xkk
            x = (opcode & 0x0F00) >> 8 # shift by one byte to left 0x0F00 -> 0x000F
            kk = opcode & 0x00FF
            V[x] = kk 
            print(f'{hex_opcode} LD V{x} {kk}')
               

        case 0x7000: # 7xkk V[x] += kk
            x = (opcode & 0x0F00) >> 8
            kk = opcode & 0x00FF
            V[x] = (V[x] + kk) & 0xFF
            print(f'{hex_opcode} ADD V{x} {kk}')

             

        case 0x8000:
            x = (opcode & 0x0F00) >> 8
            y = (opcode & 0x00F0) >> 4
            match opcode & 0x000F:
                case 0x0000:
                    V[x] = V[y]
                    print(f'{hex_opcode} LD V{x} {V[y]}')
                case 0x0001:
                    print(f'{hex_opcode} not handled')
                case 0x0002:
                    V[x] = V[x] & V[y] 
                    print(f'{hex_opcode} AND V{x} V{y}')
                case 0x0003:
                    print(f'{hex_opcode} not handled')
                case 0x0004:
                    V[x] = (V[x] + V[y]) & 0x00FF
                    if V[x] > 255:
                        V[0xF] = 1
                    else:
                        V[0xF] = 0
                    print(f'{hex_opcode} ADD {V[x]}, {V[y]}')
                case 0x0005:
                    if V[x] > V[y]:
                        V[0xF] = 1
                    else:
                        V[0xF] = 0

                    V[x] = V[x] - V[y]    

                    print(f'{hex_opcode} SUB {V[x]}, {V[y]}')
                case 0x0006:
                    print(f'{hex_opcode} not handled')
                case 0x0007:
                    print(f'{hex_opcode} not handled')
                case 0x000E:
                    print(f'{hex_opcode} not handled')

            
        case 0x9000:
            print(f'{hex_opcode} not handled')

            pass
        case 0xA000: # Annn
            I = opcode & 0x0FFF
            print(f'{hex_opcode} LD I {I}')

              

        case 0xB000:
            print(f'{hex_opcode} not handled')
            pass
        case 0xC000:
            x = (opcode & 0x0F00) >> 8
            kk = opcode & 0x00FF
            V[x] = random.randint(0,256) & kk
            print(f'{hex_opcode} RND V{x} & {kk}')
            

        case 0xD000: # to implement
            x = V[(opcode & 0x0F00) >> 8] % 64
            y = V[(opcode & 0x00F0) >> 4] % 32
            n =  (opcode & 0x000F) 
            V[0xF] = 0
            for i in range(n):
                line = MEMORY[I+ i]
                for j in range(0,8):
                    pixel = line & (0x80 >> j)
                    if pixel != 0:
                        totalX = x + j
                        totalY = y + i
                        index = totalY * 64 + totalX
                        if DISPLAY[index] == 1:
                            V[0xF] == 1
                        DISPLAY[index] ^= 1
            


        case 0xE000:
            match ( opcode & 0xF000):
                case 0x009E:
                    # key = (opcode & 0x0F00) >> 8 
                    print(f'{hex_opcode} not handled')
                    pass
                case 0x00A1:
                    print(f'{hex_opcode} not handled')
                    pass
            
        case 0xF000:
            x = (opcode & 0x0F00) >> 8 
            match (opcode & 0x00FF):
                case 0x0007:
                    V[x] = DELAY_TIMER 
                    print(f'{hex_opcode} LD V{x} DT')

                    
                case 0x000A:
                    print(f'{hex_opcode} not handled')
                    pass
                case 0x0015:
                    DELAY_TIMER = 0
                    print(f'{hex_opcode} LD DT {V[x]}')

                    
                    
                case 0x0018:
                    SOUND_TIMER = V[x]
                    print(f'{hex_opcode} LD ST, {V[x]}')
                    
                case 0x001E:
                    print(f'{hex_opcode} not handled')
                    
                case 0x0029:
                    character = V[x]
                    I = (0x050 + (character * 5))
                    
                   
                case 0x0033: # BCD representation of Vx in memory locations I , I + 1, I + 2 
                    value = V[x]
                    hundreds = (value - (value % 100)) / 100
                    value -= hundreds * 100
                    tens = (value - (value % 10)) / 10
                    value -= tens * 10
                    MEMORY[I]     = int(hundreds)
                    MEMORY[I + 1] = int(tens)
                    MEMORY[I + 2] = int(value)
                    print(f'{hex_opcode} BCD REPRESENTATION OF {V[x]} is {hundreds, tens, value}')
                    
                    

                case 0x0055:
                    print(f'{hex_opcode} not handled')
                    pass
                case 0x0065:
                    print(f'{hex_opcode}  LD Vx, [I]')
                    for i in range(0,x):
                        V[i] = MEMORY[I + i]
                    I += x + 1  

                
        
                  
                    

            






def draw(): # SDL2 or PYGAME or TKINTER
    SCREEN_DEPTH = 0
    global running

    """draw on screen the pixels listed on DISPLAY with black for 0s and white for 1s"""
    global DISPLAY
    SCALE = 20
    # pygame.display.set_mode([640, 320], HWSURFACE | DOUBLEBUF, SCREEN_DEPTH, vsync=False)
    pygame.init()
    screen = pygame.display.set_mode([64*SCALE, 32*SCALE], HWSURFACE | DOUBLEBUF, SCREEN_DEPTH, vsync=0)
    pygame.display.set_caption("YET ANOTHER CHIP-8 EMULATOR")
    screen.fill('black')
    black = (0,0,0) 
    white = (255, 255, 255) 
    clock = pygame.time.Clock()


    for i in range(len(DISPLAY)):
        if DISPLAY[i] == 1:
            color = white
        elif  DISPLAY[i] == 0:
            color = black
        x = (i % 64)
        # y = math.floor(i / 64)
        y = math.floor(i / 64)
       
        rect = pygame.Rect(x * SCALE, y * SCALE , SCALE, SCALE)        
        pygame.draw.rect(screen, color, rect )        
    pygame.display.update()
    clock.tick(60) 
    
        



