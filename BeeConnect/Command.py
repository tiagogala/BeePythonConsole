#!/usr/bin/env python

r"""
BeeCommand Class

This class exports some methods with predefined commands to control the BTF

__init__()        Initializes current class
isConnected()    returns the connection state
startPrinter()    Initializes the printer in firmware mode
getStatus()        returns the status of the printer
beep()            beep during 2s
home()            Homes axis XYZ
homeXY()          Homes axis XY
homeZ()            Homes Z axis
move(x,y,z,e)        Relatie move of axis XYZE at given feedrate
GoToFirstCalibrationPoint()    Moves the BTF to the first calibration point
GoToSecondCalibrationPoint()    Saves calibration offset and moves to second calibration point
GoToThirdCalibrationPoint()    Moves the BTF to the third calibration point
GetNozzleTemperature(T)        Defines nozzle target setpoint temperature
SetNozzleTemperature()        Returns current nozzle temperature
Load()                        Performs load filament operation
Unload()                        Performs unload filament operation
GoToHeatPos()                Moves the BTF to its heat coordinates during filament change
GoToRestPos()                Moves the BTF to its Rest coordinates
GetBeeCode()                Get current filament beecode
SetBeeCode(A)                Set current filament beecode
initSD()                    Initializes SD card
CreateFile(f)                Creates SD file
OpenFile(f)                    Opens file in the SD card
StartTransfer(f,a)            prepares the printer to receive a block of messages
startSDPrint()                Starts printing selected sd file
cancleSDPrint()                Cancels SD print
sendBlock()                    Sends a block of messages
sendBlockMsg()                Sends a message from the block
cleanBuffer()                Clears communication buffer 
getPrintStatus()                Gets print status
"""

__author__ = "BVC Electronic Systems"
__license__ = ""

import usb.core
import usb.util
import sys
import os
import time
import time
import math

import BeeConnect.Connection

class Cmd():
    
    connected = None
    beeCon = None
    
    MESSAGE_SIZE = 512
    BLOCK_SIZE = 64
    
    transmisstionErrors = 0

    """*************************************************************************
                                Init Method 
    
    *************************************************************************"""
    def __init__(self, con):
        r"""
        Init Method
        
        Initializes this class
        
        receives as argument the BeeConnection object and verifies the 
        connection status
        
        """
        
        self.beeCon = con
        self.connected = self.beeCon.isConnected()
        
        return
    
    """*************************************************************************
                                connected Method 
    
    *************************************************************************"""
    def isConnected(self):
        r"""
        isConnected method
        
        return the sate of the BTF connection:
            connected = True
            disconnected = False
        """
        return self.connected
    
    """*************************************************************************
                                Start Printer Method 
    
    *************************************************************************"""
    def startPrinter(self):
        r"""
        startPrinter method
        
        Initializes the printer in firmware mode
        """
        
        resp = self.beeCon.sendCmd("M625\n")
        
        if('Bad M-code 625' in resp):   #printer in bootloader mode
            print("Printer running in Bootloader Mode")
            print("Changing to firmware")
            self.beeCon.write("M630\n")
            self.beeCon.close()
            time.sleep(1)
            
            return "Bootloader"
        elif('ok Q' in resp):
            print("Printer running in firmware mode")
            return "Firmware"
        else:
            return ""
        
        return
    
    """*************************************************************************
                                getStatus Method 
    
    *************************************************************************"""
    def getStatus(self):
        r"""
        getStatus method
        
        returns the current status of the printer
        """
        
        resp = self.beeCon.sendCmd("M625\n")
        #print(resp)
        
        sPos = resp.find('S:')
        
        try:
            status = int(resp[sPos+2])
        except:
            return "Unknown"
        
        if(status == 3):
            return "Ready"
        elif(status == 4):
            return "Moving"
        elif(status == 5):
            return "SD_Print"
        elif(status == 6):
            return "Transfer"
        elif(status == 7):
            return "Pause"
        elif(status == 9):
            return "SDown_Wait"
        
        return "Unknown"

    """*************************************************************************
                                beep Method 
    
    *************************************************************************"""
    def beep(self):
        r"""
        beep method
        
        performs a beep with 2 seconds duration
        """
        
        self.beeCon.sendCmd("M300 P2000\n")
        
        return

    """*************************************************************************
                                home Method 
    
    *************************************************************************"""
    def home(self):
        r"""
        home method
        
        homes all axis
        """
        
        self.beeCon.sendCmd("G28\n","3")
        
        return
    
    """*************************************************************************
                                homeXY Method 
    
    *************************************************************************"""
    def homeXY(self):
        r"""
        homeXY method
        
        home axis X and Y
        """
        
        self.beeCon.sendCmd("G28 X0 Y0\n","3")
        
        return
    
    """*************************************************************************
                                homeZ Method 
    
    *************************************************************************"""
    def homeZ(self):
        r"""
        homeZ method
        
        homes Z axis
        """
        
        self.beeCon.sendCmd("G28 Z0\n","3")
        
        return
    
    """*************************************************************************
                                move Method 
    
    *************************************************************************"""
    def move(self,x=None,y=None,z=None,e=None,f=None):
        r"""
        move method
        
        performs a relative move at a given feedrate current
        
        arguments:
        x - X axis displacement
        y - Y axis displacement
        z - Z axis displacement
        e - E extruder displacement
        
        f - feedrate
        
        """
        resp = self.beeCon.sendCmd("M121\n")
        #print(resp)
        
        splits = resp.split(" ")
        xSplit = splits[2].split(":")
        ySplit = splits[3].split(":")
        zSplit = splits[4].split(":")
        eSplit = splits[5].split(":")
        
        currentX = float(xSplit[1])
        currentY = float(ySplit[1])
        currentZ = float(zSplit[1])
        currentE = float(eSplit[1])
        
        newX = currentX
        newY = currentY
        newZ = currentZ
        newE = currentE
        
        commandStr = ""
        
        if x is not None:
            newX = newX + x
        if y is not None:
            newY = newY + y
        if z is not None:
            newZ = newZ + z
        if e is not None:
            newE = newE + e
            
            
        if f is not None:
            newF = float(f)
            commandStr = "G1 X" + str(newX) + " Y" + str(newY) + " Z" + str(newZ) + " E" + str(newE) + "F" + str(newF) + "\n"
        else:
            commandStr = "G1 X" + str(newX) + " Y" + str(newY) + " Z" + str(newZ) + " E" + str(newE) + "\n"
        
        
        
        self.beeCon.sendCmd(commandStr,"3")
        
        return
    
    """*************************************************************************
                                GoToFirstCalibrationPoint Method 
    
    *************************************************************************"""
    def GoToFirstCalibrationPoint(self):
        r"""
        GoToFirstCalibrationPoint method
        
        moves the printer to the first calibration point
        """
        
        #go to home
        self.beeCon.sendCmd("G28\n","3")
        
        #set feedrate
        resp = self.beeCon.sendCmd("G1 F15000\n")
        #print(resp)
        
        #set acceleration
        resp = self.beeCon.sendCmd("M206 X400\n")
        #print(resp)
        
        #go to first point
        self.beeCon.sendCmd("G1 X0 Y67 Z2\n")
        
        #set acceleration
        resp = self.beeCon.sendCmd("M206 X1000\n","3")
        #print(resp)
        
        return
    
    """*************************************************************************
                                GoToSecondCalibrationPoint Method 
    
    *************************************************************************"""
    def GoToSecondCalibrationPoint(self):
        r"""
        GoToSecondCalibrationPoint method
        
        Saves calibration offset and moves to second calibration point
        """
        
        #record calibration position
        self.beeCon.sendCmd("M603\n")
        self.beeCon.sendCmd("M601\n")
        
        #set feedrate
        self.beeCon.sendCmd("G1 F5000\n")
        #set acceleration
        self.beeCon.sendCmd("M206 X400\n")
        
        
        #go to SECOND point
        self.move(0,0,10,0)
        resp = self.beeCon.sendCmd("G1 X-31 Y-65\n","3")
        self.move(0,0,-10,0)
        
        return
    
    """*************************************************************************
                                GoToThirdCalibrationPoint Method 
    
    *************************************************************************"""
    def GoToThirdCalibrationPoint(self):
        r"""
        GoToThirdCalibrationPoint method
        
        moves the printer to the third calibration point
        """
        
        #set feedrate
        self.beeCon.sendCmd("G1 F5000\n")
        #set acceleration
        self.beeCon.sendCmd("M206 X400\n")
        
        self.move(0,0,10,0)
        #go to SECOND point
        self.beeCon.sendCmd("G1 X35 Y-65\n","3")
        
        self.move(0,0,-10,0)
        
        return
    
    """*************************************************************************
                                GetNozzleTemperature Method 
    
    *************************************************************************"""
    def GetNozzleTemperature(self):
        r"""
        GetNozzleTemperature method
        
        reads current nozzle temperature
        
        returns:
            nozzle temperature
        """
        
        #get Temperature
        resp = self.beeCon.sendCmd("M105\n")
        #print(resp)
        
        try:
            splits = resp.split(" ")
            tPos = splits[0].find("T:")
            t = float(splits[0][tPos+2:])
            return t
        except:
            pass
        
        return 0

    """*************************************************************************
                                SetNozzleTemperature Method 
    
    *************************************************************************"""
    def SetNozzleTemperature(self, t):
        r"""
        SetNozzleTemperature method
        
        Sets nozzle target temperature
        
        Arguments:
            t - nozzle temperature
        """
        
        commandStr = "M104 S" + str(t) + "\n"
        
        #set Temperature
        resp = self.beeCon.sendCmd(commandStr)
        #print(resp)
        
        return
    
    """*************************************************************************
                                Load Method 
    
    *************************************************************************"""
    def Load(self):
        r"""
        load method
        
        performs load filament operation
        """
        
        self.beeCon.sendCmd("G92 E\n")
        self.beeCon.sendCmd("M300 P500\n")
        self.beeCon.sendCmd("M300 S0 P500\n")
        self.beeCon.sendCmd("M300 P500\n")
        self.beeCon.sendCmd("M300 S0 P500\n")
        self.beeCon.sendCmd("M300 P500\n")
        self.beeCon.sendCmd("M300 S0 P500\n")
        self.beeCon.sendCmd("G1 F300 E100\n")
        self.beeCon.sendCmd("G92 E\n")
        return

    """*************************************************************************
                                Unload Method 
    
    *************************************************************************"""
    def Unload(self):
        r"""
        Unload method
        
        performs unload operation
        """
        
        self.beeCon.sendCmd("G92 E\n")
        self.beeCon.sendCmd("M300 P500\n")
        self.beeCon.sendCmd("M300 S0 P500\n")
        self.beeCon.sendCmd("M300 P500\n")
        self.beeCon.sendCmd("M300 S0 P500\n")
        self.beeCon.sendCmd("M300 P500\n")
        self.beeCon.sendCmd("M300 S0 P500\n")
        self.beeCon.sendCmd("G1 F300 E50\n")
        self.beeCon.sendCmd("G92 E\n")
        self.beeCon.sendCmd("G1 F1000 E-23\n","3")
        self.beeCon.sendCmd("G1 F800 E2\n","3")
        self.beeCon.sendCmd("G1 F2000 E-23\n","3")
        self.beeCon.sendCmd("G1 F200 E-50\n","3")
        self.beeCon.sendCmd("G92 E\n")
        
        return

    """*************************************************************************
                                GoToHeatPos Method 
    
    *************************************************************************"""
    def GoToHeatPos(self):
        r"""
        GoToHeatPos method
        
        moves the printer to the heating coordinates
        """
        
        #set feedrate
        self.beeCon.sendCmd("G1 F15000\n")
        
        #set acceleration
        self.beeCon.sendCmd("M206 X400\n")
        
        #go to first point
        self.beeCon.sendCmd("G1 X30 Y0 Z10\n")
        
        #set acceleration
        self.beeCon.sendCmd("M206 X1000\n","3")
        
        return

    """*************************************************************************
                                GoToRestPos Method 
    
    *************************************************************************"""
    def GoToRestPos(self):
        r"""
        GoToRestPos method
        
        moves the printer to the rest position
        """
        
        #set feedrate
        self.beeCon.sendCmd("G1 F15000\n")
        
        #set acceleration
        self.beeCon.sendCmd("M206 X400\n")
        
        #go to first point
        self.beeCon.sendCmd("G1 X-50 Y0 Z110\n")
        
        #set acceleration
        self.beeCon.sendCmd("M206 X1000\n","3")
        
        return
    
    """*************************************************************************
                                GetBeeCode Method 
    
    *************************************************************************"""
    def GetBeeCode(self):
        r"""
        GetBeeCode method
        
        reads current filament BeeCode
        
        returns:
            Filament BeeCode
        """
        
        #Get BeeCode
        resp = self.beeCon.sendCmd("M400\n")
        
        splits = resp.split(" ")
        
        code = ""
        
        for s in splits:
            cPos = s.find("bcode")
            if(cPos >= 0):
                code = s[cPos+6:]
        
        
        return code

    """*************************************************************************
                                SetBeeCode Method 
    
    *************************************************************************"""
    def SetBeeCode(self, code):
        r"""
        SetBeeCode method
        
        Sets filament beecode
        
        arguments:
            code - filament code
        """
        
        commandStr = "M400 " + code + "\n"
        
        #Set BeeCode
        self.beeCon.sendCmd(commandStr)
        
        return

    """*************************************************************************
                                initSD Method 
    
    *************************************************************************"""
    def initSD(self):
        r"""
        initSD method
        
        inits Sd card
        """
        #Init SD
        self.beeCon.write("M21\n")
        
        tries = 10
        resp = ""
        while((tries > 0) and ("ok" not in resp.lower())):
            try:
                resp += self.beeCon.read()
                tries -= 1
            except:
                pass
        
        return tries
    
    """*************************************************************************
                                getFileList Method 
    
    *************************************************************************"""
    def getFileList(self):
        
        fList = {}
        fList['FileNames'] = []
        fList['FilePaths'] = []
        
        self.initSD()

        resp = ""
        self.beeCon.write("M20\n")
            
        while("end file list" not in resp.lower()):
            resp += self.beeCon.read()
        
        lines = resp.split('\n')
        
        for l in lines:
            
            if("/" in l):
                if("firmware.bck" in l.lower()):
                    pass
                elif("firmware.bin" in l.lower()):
                    pass
                elif("config.txt" in l.lower()):
                    pass
                elif("config.bck" in l.lower()):
                    pass
                elif(l == ""):
                    pass
                else:
                    fName = l[1:len(l)-1]
                    fList['FileNames'].append(fName)
                    fList['FilePaths'].append('')
                    
            elif("end file list" in l.lower()):
                return fList
            
        return fList
        
    """*************************************************************************
                                CraeteFile Method 
    
    *************************************************************************"""
    def CraeteFile(self, fileName):
        r"""
        CraeteFile method
        
        Creates a file in the SD card root directory
        
        arguments:
            fileName - file name
        """
        #Init SD
        self.initSD()
        
        fn = fileName
        if(len(fileName) > 8):
            fn = fileName[:8]
        
        cmdStr = "M30 " + fn + "\n"
        
        resp = self.beeCon.sendCmd(cmdStr)

        tries = 10
        while(tries > 0):
            
            if("file created" in resp.lower()):
                print("   :"" SD file created")
                break
            elif("error" in resp.lower()):
                print("   : Error creating file")
                return False
            else:
                resp = self.beeCon.sendCmd("\n")
                #print(resp,"...")
            
            tries -= 1
        if(tries <= 0):
            return False
        
        return True

    """*************************************************************************
                                OpenFile Method 
    
    *************************************************************************"""
    def OpenFile(self, fileName):
        r"""
        OpenFile method
        
        opens file in the sd card root dir
        
        arguments:
            fileName - file name
        """
        
        #Init SD
        self.initSD()
        
        cmdStr = "M23 " + fileName + "\n"
        
        #Open File
        resp = self.beeCon.sendCmd(cmdStr)
        
        tries = 10
        while(tries > 0):
            if("file opened" in resp.lower()):
                print("   :"" SD file opened")
                break
            else:
                resp = self.beeCon.sendCmd("\n")
            tries -= 1
        
        if(tries <= 0):
            return False
        
        return True
    
    """*************************************************************************
                                StartTransfer Method 
    
    *************************************************************************"""
    def StartTransfer(self, fSize, a):
        r"""
        StartTransfer method
        
        prepares the printer to receive a block of messages
        
        arguments:
            fSize - bytes to be writen
            a - initial write position
        """
        
        cmdStr = "M28 D" + str(fSize - 1) + " A" + str(a) + "\n"
        #waitStr = "will write " + str(fSize) + " bytes ok"
        
        resp = self.beeCon.sendCmd(cmdStr)
        
        tries = 10
        while((tries > 0) and ("ok" not in resp.lower())):
            resp += self.beeCon.sendCmd("dummy")
            tries -= 1
        
        #print("   :",resp)
        
        if(tries <= 0):
            return False
        
        return True

    """*************************************************************************
                                startSDPrint Method 
    
    *************************************************************************"""
    def startSDPrint(self):
        r"""
        startSDPrint method
        
        starts printing selected file
        """
        
        self.beeCon.sendCmd("M33\n")
        
        return True

    """*************************************************************************
                                cancelSDPrint Method 
    
    *************************************************************************"""
    def cancelSDPrint(self):
        r"""
        cancelSDPrint method
        
        cancels current print and home the printer axis
        """
        
        print('Cancelling print')
        self.beeCon.write("M112\n",100)
        print(self.beeCon.read(100))
        
        self.beeCon.write("G28 Z \n",100)
        self.beeCon.read(100)
        
        self.beeCon.write("G28\n",100)
        print(self.beeCon.read(100))
        
        print(self.beeCon.read())
        
        #self.beeCon.read()
        #self.homeZ()
        #self.homeXY()
        
        return True

    """*************************************************************************
                            sendBlock Method 

    *************************************************************************"""
    def sendBlock(self,startPos, fileObj):
        r"""
        sendBlock method
        
        writes a block of messages
        
        arguments:
            startPos - starting position of block
            fileObj - file object with file to write
            
        returns:
            True if block transfered successfully
            False if an error occurred and communication was reestablished
            None if an error occurred and could not reestablish communication with printer
        """
        
        fileObj.seek(startPos)
        block2write = fileObj.read(self.MESSAGE_SIZE*self.BLOCK_SIZE)
        
        endPos = startPos + len(block2write)
        
        #self.StartTransfer(endPos,startPos)
        self.beeCon.write("M28 D" + str(endPos - 1) + " A" + str(startPos) + "\n")
        
        nMsg = math.ceil(len(block2write)/self.MESSAGE_SIZE)
        msgBuf = []
        for i in range(nMsg):
            if(i < nMsg):
                msgBuf.append(block2write[i*self.MESSAGE_SIZE:(i+1)*self.MESSAGE_SIZE])
            else:
                msgBuf.append(block2write[i*self.MESSAGE_SIZE:])
        
        resp = self.beeCon.read()
        while("ok q:0" not in resp.lower()):
            resp += self.beeCon.read()
        #print(resp)
        #resp = self.beeCon.read(10) #force clear buffer
        
        for m in msgBuf:
            mResp = self.sendBlockMsg(m)
            if(mResp is not True):
                return mResp
        
        return True

    """*************************************************************************
                            sendBlockMsg Method 

    *************************************************************************"""
    def sendBlockMsg(self,msg):
        r"""
        sendBlockMsg method
        
        sends a block message to the printer.
        
        arguments:
            msg - message to be writen
        
        returns:
            True if message transfered successfully
            False if an error occurred and communication was reestablished
            None if an error occurred and could not reestablish communication with printer
        """
        
        #resp = self.beeCon.dispatch(msg)
        msgLen = len(msg)
        bWriten = self.beeCon.write(msg)
        if(msgLen != bWriten):
            print("Bytes lost")
            return False
        
        time.sleep(0.001)
        
        tries = 10
        resp = ""
        while((tries > 0) and ("tog" not in resp)):
            try:
                resp += self.beeCon.read()
                tries -= 1
            except Exception:
                tries = -1
        
        if(tries > 0):
            return True
        else:
            cleaningTries = 5
            clean = False
            self.transmisstionErrors += 1
            while(cleaningTries > 0 and clean == False):
                clean = self.cleanBuffer()
                time.sleep(0.5)
                self.beeCon.close()
                self.beeCon = None
                self.beeCon = BeeConnect.Connection.Con()
                
                cleaningTries -= 1
            
            if(cleaningTries <= 0):
                return None
            
            if(clean == False):
                return None
            
            return False

    """*************************************************************************
                            cleanBuffer Method 

    *************************************************************************"""
    def cleanBuffer(self):
        r"""
        cleanBuffer method
        
        cleans communication buffer with printer
        """
        
        cleanStr = "M625" + "a"*(self.MESSAGE_SIZE-5) + "\n"
        
        self.beeCon.write(cleanStr,50)
        
        tries = self.BLOCK_SIZE + 1
        
        resp = self.beeCon.read(50)
        acc_resp = ""
        #resp = ""
        
        while("ok" not in acc_resp.lower() and tries > 0):
            print("Cleaning")
            try:
                self.beeCon.write(cleanStr,25)
                self.beeCon.write("",25)
                resp = self.beeCon.read(25)
                acc_resp += resp
                print(resp)
                tries -= 1
            except Exception:
                print("Read timeout")
                tries = 0
        
        print(resp)
        
        return tries
    
    """*************************************************************************
                            getPrintStatus Method 

    *************************************************************************"""
    def getPrintStatus(self):
        
        printStatus = {}
        
        self.beeCon.write('M32\n')
        
        resp = ""
        
        while('ok' not in resp):
            resp += self.beeCon.read()
        
        split = resp.split(' ')
        
        for s in split:
            if('A' in s):
                printStatus['Estimated Time'] = int(s[1:])
            elif('B' in s):
                printStatus['Elapsed Time'] = int(s[1:])/(60*1000)
            elif('C' in s):
                printStatus['Lines'] = int(s[1:])
            elif('D' in s):
                printStatus['Executed Lines'] = int(s[1:])
        
        return printStatus
    
    """*************************************************************************
                                FlashFirmware Method 
    
    
    *************************************************************************"""
    def FlashFirmware(self, fileName):
        
        if(os.path.isfile(fileName) == False):
            print("   :","File does not exist")
            return
        
        print("   :","Flashing new firmware File: ",fileName)
        
        cTime = time.time()
        
        message = "M650 A{0}\n".format(os.path.getsize(fileName))
        self.beeCon.write(message)
        
        resp = ''
        while('ok' not in resp):
            resp += self.beeCon.read()
        
        resp = ''
        with open(fileName, 'rb') as f:
            while True:
                buf = f.read(64)
                
                if not buf: break
                
                self.beeCon.write(buf)
                ret = []
                while (len(ret) != len(buf)):
                    try:
                        ret += self.beeCon.ep_in.read(len(buf), 1000)
                    except usb.core.USBError as e:
                        if ("timed out" in str(e.args)):
                            pass
            
                bRet = bytes(ret)
                if(bRet not in buf):
                    print('TODO: MANAGE FIRMWARE FLASHING FAILURE')
                    return

                sys.stdout.write('.')
                sys.stdout.flush()

        eTime = time.time()
        
        avgSpeed = os.path.getsize(fileName)//(eTime - cTime)
        
        print ("\n   :","Flashing completed in", eTime-cTime, 's')
        print("   :Average Transfer Speed",avgSpeed)
        
        
        return
        