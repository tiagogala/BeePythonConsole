'''
Created on Feb 5, 2015

@author: mgomes
'''

import Console
import os
import sys
import time

done = False

def restart_program():
    python = sys.executable
    os.execl(python, python, * sys.argv)


if __name__ == "__main__":
    
    done = False
    
    console = Console.Console()
    
    if(console.exit):
        if(console.exitState == "restart"):
            try:
                console.beeCon.close()
            except:
                pass
            console = None
            restart_program()
    
    while(done == False):
        var = input(">:")
        #print(var)
        
        if("exit" in var.lower()):
            console.close()
            console = None
            done = True
            
        elif("mode" in var.lower()):
            print("   :",console.mode)
            
        elif("-gcode" in var.lower() and console.mode == "firmware"):
            print("   :","Starting gcode trasnfer:")
            if("-gcode -c" in var.lower() and console.mode == "firmware"):
                print("   :","Editing gCode :")
                console.transferGCodeWithColor(var)
            else:
                console.transferGCode(var)
                
        elif("-load" in var.lower()):
            print("   :","Loading filament")
            console.load()
            
        elif("-unload" in var.lower()):
            print("   :","Unoading filament")
            console.unload()
        elif("-estimate" in var.lower()):
            print("   :","Estimating time")
            console.estimateTime(var)
        elif("-flash" in var.lower()):
            print("   :","Flashing Firmware")
            console.FlashFirmware(var)
        else:
            if(("m630" in var.lower() and console.mode == "bootloader") or ("m609" in var.lower() and console.mode == "firmware")):
                print("Changing to firmware/bootloader")
                #console.goToFirmware()
                console.sendCmd(var)
                try:
                    console.beeCon.close()
                except:
                    pass
                console = None
                time.sleep(1)
                restart_program()
            else:
                console.sendCmd(var)