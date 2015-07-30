#!/usr/bin/env python3
"""
* Copyright (c) 2015 BEEVC - Electronic Systems This file is part of BEESOFT
* software: you can redistribute it and/or modify it under the terms of the GNU
* General Public License as published by the Free Software Foundation, either
* version 3 of the License, or (at your option) any later version. BEESOFT is
* distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
* without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
* PARTICULAR PURPOSE. See the GNU General Public License for more details. You
* should have received a copy of the GNU General Public License along with
* BEESOFT. If not, see <http://www.gnu.org/licenses/>.
"""

r"""
BeePythonConsole - Terminal console for the BeeTheFirst 3D Printer

Every new line inserted in the console is processed in 2 different categories:

Printer commands:
    Single M & G code lines.

Operation Commands:
    Commands to do specific operations, like load filament and transfer files.
    Operation commands always start with an "-"
    
    The following operation commands are implemented:
    
    * "-load" Load filament operation
    * "-unload" Unload filament operation
    * "-gcode LOCALFILE_PATH R2C2_FILENAME" Transfer gcode file to Printer.
                    
                    LOCALFILE_PATH -> filepath to file
                    R2C2_FILENAME -> Name to be used when writing in printer memory (Optional)
    
    * "-flash LOCALFILE_PATH" Flash firmware.
    
                    LOCALFILE_PATH -> filepath to file

    * "-exit" Closes console


"""

__author__ = "BVC Electronic Systems"
__license__ = ""

import Console
import os
import sys
import time

done = False

newestFirmwareVersion = 'MSFT-BEETHEFIRST-10.1.0'
fwFile = 'MSFT-BEETHEFIRST-Firmware-10.1.0.BIN'

def restart_program():
    python = sys.executable
    os.execl(python, python, * sys.argv)


if __name__ == "__main__":
    
    done = False
    
    console = Console.Console()
    command_list = []
	
    if(console.exit):
        if(console.exitState == "restart"):
            try:
                console.beeCon.close()
            except:
                pass
            console = None
            restart_program()
    
	#process args
    if len(sys.argv)==2:
        if len(sys.argv) == 2 and os.path.isfile(sys.argv[1]):
            print("Reading", sys.argv[1])
            with open(sys.argv[1]) as f:
                command_list=f.readlines()
    while(done == False):
        if len(sys.argv) >= 2 and os.path.isfile(sys.argv[1])==False: # process gcode list
            sys.argv.pop(0) #clear first record (program name)
            var = " ".join(sys.argv)
            done = True

        if len(command_list) >= 1:            # end processing gcode list from file 
            var = command_list.pop(0)
            print(var)
            if len(command_list) == 0:
                done=True
        else:
            var = input(">:")
			#print(var)
        
        if("-exit" in var.lower()):
            console.close()
            console = None
            done = True
            
        elif("mode" in var.lower()):
            print("   :",console.mode)
            
        elif("-gcode" in var.lower() and console.mode == "firmware"):
            print("   :","Starting gcode transfer:")
            if("-gcode -c" in var.lower() and console.mode == "firmware"):
                print("   :","Editing gCode :")
                console.transferGCodeWithColor(var)
            else:
                console.transferGCode(var)
                
        elif("-load" in var.lower()):
            print("   :","Loading filament")
            console.load()
            
        elif("-unload" in var.lower()):
            print("   :","Unloading filament")
            console.unload()
        elif("-estimate" in var.lower()):
            print("   :","Estimating time")
            console.estimateTime(var)
        elif("-flash" in var.lower()):
            print("   :","Flashing Firmware")
            console.FlashFirmware(var)
        elif("-verify" in var.lower()):
            print("   :Newest Printer Firmware Available:",newestFirmwareVersion)
            currentVersionResp = console.sendCmd('M115',printReply=False)       #Ask Printer Firmware Version
            if(newestFirmwareVersion in currentVersionResp):
                print("   :Printer is already running the latest firmware")
            else:
                printerModeResp = console.sendCmd('M116',printReply=False)      #Ask Printer Bootloader Version
                if('Bad M-code' in printerModeResp):                            #Firmware Does not reply to M116 command, Bad M-Code Error
                    print("   :Printer in Firmware, restarting your Printer to Bootloader")
                    console.sendCmd('M609',printReply=False)                    #Send Restart Command to Firmware
                    time.sleep(2)                                               #Small delay to make sure the board resets and establishes connection
                    #After Reset we must close existing connections and reconnect to the new device
                    while(True):
                        try:
                            console.beeCon.close()      #close old connection
                            console = None
                            console = Console.Console() #search for printer and connect to the first
                            if(console.connected == True):  #if connection is established proceed
                                break                       
                        except:
                            pass
                    
                else:
                    print("   :Printer is in Bootloader")
                    
                console.beeCmd.FlashFirmware(fwFile)                        #Flash New Firmware
                newFwCmd = 'M114 A' + newestFirmwareVersion                 #preprare command string to set Firmware String
                console.sendCmd(newFwCmd, printReply=False)                 #Record New FW String in Bootloader
            #console.FlashFirmware(var)
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
