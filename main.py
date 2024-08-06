from chip import *
import os
import random
import time

def main():
    try:
        file = input('rom: ')
    except FileNotFoundError:
        file = 'roms/chip-logo.c8'

    running = True
    # load rom to memory at starting position 0x200
    rom = loadrom(file)
    for offset in range(len(rom)):
        MEMORY[0x200 + offset] = rom[offset]

    # load fontset to memory at starting position 0x50
    for offset in range(len(FONTSET)):
        MEMORY[0x050 + offset] = FONTSET[offset] 


    while running:
        # fetch-decode-execute  
        cpu()
        draw() 
        for event in pygame.event.get(): # close window 
            if event.type == pygame.QUIT:
                running = False
        
        




if __name__ == "__main__":
    main()

