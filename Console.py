# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.
#from chardet.test import result
#import cmd
from gcoder import GCode

__author__ = "mgomes"
__date__ = "$Jan 8, 2015 11:20:21 AM$"

import BeeConnect.Command
import BeeConnect.Connection
import time
import os
import math
import usb.core
import subprocess
import sys
import gcoder
import re

class Console():
    
    beeCon = None
    beeCmd = None
    
    connected = False
    exit = False
    
    exitState = None
    
    mode = "None"
    
    """*************************************************************************
                                Init Method 
    
    
    *************************************************************************"""
    def __init__(self):
        
        self.connected = False
        self.exit = False
        self.exitState = None
        
        nextPullTime = time.time() + 0.05
        
        while (not self.connected) and (not self.exit):
            
            t = time.time()
            if t > nextPullTime:
                print("Wait for connection")
                
                self.beeCon = BeeConnect.Connection.Con()
                if(self.beeCon.isConnected() == True):
                    self.beeCmd = BeeConnect.Command.Cmd(self.beeCon)
                    resp = self.beeCon.sendCmd("M625\n")
                    if('Bad M-code 625' in resp):   #printer in bootloader mode
                        print("Printer running in Bootloader Mode")
                        self.mode = "bootloader"
                        self.connected = True
                    elif('ok Q' in resp):
                        print("Printer running in firmware mode")
                        self.mode = "firmware"
                        self.connected = True
                    else:
                        cmdStr = "M625\n;" + "a"*507
                        tries = 32
                        print("Cleaning buffer")
                        
                        resp = self.beeCmd.cleanBuffer()
                        
                        if(resp == 0):
                            print("error connecting to printer... restarting application")
                            self.beeCon.close()
                            self.beeCon = None
                            self.exit = True
                            self.exitState = "restart"
                            return
                        
                        """
                        while(tries > 0):
                            try:
                                resp = self.beeCon.sendCmd(cmdStr,None,50)
                            except:
                                pass
                            tries -= 1
                        """
                        self.beeCon.close()
                        self.beeCon = None
                        #return None
                    
                nextPullTime = time.time() + 0.05
                
        return

    """*************************************************************************
                                goToFirmware Method 
    
    
    *************************************************************************"""
    def goToFirmware(self):
        
        self.connected = False
        self.exit = False
        
        self.beeCon.close()
        self.beeCon = None
        
        self.beeCmd = None
        
        nextPullTime = time.time() + 0.1
        
        while (not self.connected) and (not self.exit):
            
            t = time.time()
            if t > nextPullTime:
                
                self.beeCon = BeeConnect.Connection.Con()
                if(self.beeCon.isConnected() == True):
                    self.beeCmd = BeeConnect.Command.Cmd(self.beeCon)
                    
                    resp = self.beeCmd.startPrinter()
                
                    if('Firmware' in resp):
                        self.connected = self.beeCon.connected
                        self.mode = "firmware"
                        return
                    elif('Bootloader' in resp):
                        self.beeCon = None
                    
                nextPullTime = time.time() + 0.1
                print("Wait for connection")
        
        return

    """*************************************************************************
                                close Method 
    
    
    *************************************************************************"""
    def close(self):
        
        self.beeCon.close()
        
        print("Closing")
        
        return

    """*************************************************************************
                                sendCmd Method 
    
    
    *************************************************************************"""
    def sendCmd(self, cmd):
        
        cmdStr = cmd + "\n"
        
        wait = None
        if("g" in cmd.lower()):
            wait = "3"
        
        resp = self.beeCon.sendCmd(cmdStr, wait)
        
        splits = resp.rstrip().split("\n")
        
        for r in splits:
            print("   :",r)
            
        return resp
    
    """*************************************************************************
                                load Method 
    
    
    *************************************************************************"""
    def load(self):
        
        self.beeCmd.Load()
            
        return

    """*************************************************************************
                                unload Method 
    
    
    *************************************************************************"""
    def unload(self):
        
        self.beeCmd.Unload()
            
        return
    """*************************************************************************
                                transferGCodeWithColor Method 
    
    
    *************************************************************************"""
    def transferGCodeWithColor(self, cmd):
        
        localFN = None
        sdFN = None
        color = None
            
        fields = cmd.split(" ")
        
        if(len(fields) < 4):
            print("   :","Insuficient fields")
            return
        elif(len(fields) == 4):
            localFN = fields[2]
            sdFN = localFN
            color = fields[3]
        elif(len(fields) == 5):
            localFN = fields[2]
            sdFN = fields[3]
            color = fields[4]
        
        if(os.path.isfile(localFN) == False):
            print("   :","File does not exist")
            return
        
        colorCode = "W1"
        if("black" in color.lower()):
            colorCode = "W1"
        
        header = "M300\nG28\nM206 X500\nM107\nM104 S220\nG92 E\nM642 "
        header += str(colorCode) +"\nM130 T6 U1.3 V80\nG1 X-98.0 Y-20.0 Z5.0 F3000\n"
        header += "G1 Y-68.0 Z0.3\nG1 X-98.0 Y0.0 F500 E20\nG92 E\n"
        
        footer = "M300\nM104 S0\nG28 X\nG28 Z\nG1 Y65\nG92 E\n"
        
        f = open(localFN, 'r')
        
        localFile = f.read()
        f.close()
        
        fw = open(localFN, 'w')
        
        fw.write(header)
        fw.write(localFile)
        fw.write(footer)
        
        fw.close()
        
        self.transferGFile(localFN, sdFN)
        
        return

    """*************************************************************************
                                transferGCode Method 
    
    
    *************************************************************************"""
    def transferGCode(self, cmd):
        
        localFN = None
        sdFN = None
            
        fields = cmd.split(" ")
        
        if(len(fields) < 2):
            print("   :","Insuficient fields")
            return
        elif(len(fields) == 2):
            localFN = fields[1]
            sdFN = localFN
        elif(len(fields) == 3):
            localFN = fields[1]
            sdFN = fields[2]
        
        #check if file exists
        if(os.path.isfile(localFN) == False):
            print("   :","File does not exist")
            return
        
        #REMOVE SPECIAL CHARS
        sdFN = re.sub('[\W_]+', '', sdFN)
        
        #CHECK FILENAME
        if(len(sdFN) > 8):
            sdFN = sdFN[:7]
        
        firstChar = sdFN[0]
        
        if(firstChar.isdigit()):
            nameChars = list(sdFN)
            nameChars[0] = 'a'
            sdFN = "".join(nameChars)
        
        #ADD ESTIMATOR HEADER
        gc = gcoder.GCode(open(localFN,'rU'))
        
        est = gc.estimate_duration()
        eCmd = 'M300\n'                 #Beep
        eCmd += 'M31 A' + str(est['seconds']//60) + ' L' + str(est['lines']) + '\n' #Estimator command
        eCmd += 'M32 A0\n'      #Clear time counter
        
        newFile = open('gFile.gcode','w')
        newFile.write(eCmd)
        newFile.close()
        
        os.system("cat '" + localFN + "' >> " + "gFile.gcode")
        
        
        self.transferGFile('gFile.gcode', sdFN)
        
        
        return
    
    """*************************************************************************
                                estimateTime Method 
    
    
    *************************************************************************"""
    def estimateTime(self, cmd):
        
        localFN = None
        sdFN = None
            
        fields = cmd.split(" ")
        
        if(len(fields) < 2):
            print("   :","Insuficient fields")
            return
        elif(len(fields) == 2):
            localFN = fields[1]
            sdFN = localFN
        elif(len(fields) == 3):
            localFN = fields[1]
            sdFN = fields[2]
            
        estimator = gcoder.GCode(open(localFN, "rU"));
        est = estimator.estimate_duration()
        nLines = est['lines']
        min = est ['seconds']//60
        
        #estimatorPath = "/home/mgomes/BeePanel/estimator/gcoder.py"
        #-estimate /home/mgomes/git/BTFPythonConsole/src/pin
        #estCmd = ["python","/home/mgomes/BeePanel/estimator/gcoder.py",localFN]
        #p = subprocess.Popen(estCmd, stdout=subprocess.PIPE)
        #output = p.stdout.read()
        #outStr = str(output)
        #print(output)
        
        return
        
    """*************************************************************************
                                transferGCode Method 
    
    
    *************************************************************************"""
    def transferGFile(self, localFN, sdFN):
        
        #Load File
        print("   :","Loading File")
        f = open(localFN, 'rb')
        fSize = os.path.getsize(localFN)
        print("   :","File Size: ", fSize, "bytes")
        
        blockBytes = self.beeCmd.MESSAGE_SIZE * self.beeCmd.BLOCK_SIZE
        nBlocks = math.ceil(fSize/blockBytes)
        print("   :","Number of Blocks: ", nBlocks)
        
        #TODO RUN ESTIMATOR
        
        #CREATE SD FILE
        resp = self.beeCmd.CraeteFile(sdFN)
        if(not resp):
            return
        
        #Start transfer
        blocksTransfered = 0
        totalBytes = 0
        
        startTime = time.time()
        
        #Load local file
        with open(localFN, 'rb') as f:
            
            self.beeCmd.transmisstionErrors = 0

            while(blocksTransfered < nBlocks):
                
                startPos = totalBytes
                endPos = totalBytes + blockBytes
                
                bytes2write = endPos - startPos
                
                if(blocksTransfered == nBlocks -1):
                    endPos = fSize
                    
                blockTransfered = False
                while(blockTransfered == False):
                    blockTransfered = self.beeCmd.sendBlock(startPos,f)
                    if(blockTransfered is None):
                        print("Transfer aborted")
                        return False
                
                totalBytes += bytes2write 
                blocksTransfered += 1
                print("   :","Transfered ", str(blocksTransfered), "/", str(nBlocks), " blocks ", totalBytes, "/", fSize, " bytes")
                
        print("   :","Transfer completed",". Errors Resolved: ", self.beeCmd.transmisstionErrors)
        
        elapsedTime = time.time()- startTime
        avgSpeed = fSize//elapsedTime
        print("Elapsed time: ",elapsedTime)
        print("Average Transfer Speed: ", avgSpeed)
        
        return
    
    """*************************************************************************
                                FlashFirmware Method 
    
    
    *************************************************************************"""
    def FlashFirmware(self, cmd):
        
        split = cmd.split(' ')
        
        fileName = split[1]
        
        self.beeCmd.FlashFirmware(fileName)
        
        
        return