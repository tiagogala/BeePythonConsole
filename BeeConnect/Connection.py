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
BeeConnect Class

This class provides the methods to manage and control communication with the
BeeTheFirst 3D printer

__init__()        Initializes current class
findBEE()        Searches for connected printers and establishes connection
write(message,timeout) writes data to the communication buffer
read()            read data from the communication buffer
dispatch(message) writes data to the buffer and reads the response
sendCmd(cmd,wait,to) sends a command to the 3D printer
waitFor(cmd,s,to)        writes command to the printer and waits for the response
waitForStatus(cmd,s,to)    writes command to the printer and waits for a give printer status
close()            closes active communication with the printer
isConnected()    returns the current state of the printer connection 
"""


__author__ = "BVC Electronic Systems"
__license__ = ""

import usb
import usb.core
import usb.util
import usb.backend.libusb1 as libusb1
import usb.backend.libusb0 as libusb0
import usb.backend.openusb as openusb
import sys
import os
import time

class Con():
    
    dev = None
    endpoint = None
    ep_in = None
    ep_out = None
    cfg = None
    intf = None

    READ_TIMEOUT = 500
    DEFAULT_READ_LENGTH = 512

    queryInterval = 0.5
    
    connected = None
    
    backend = None

    """*************************************************************************
                                Init Method 
    
    *************************************************************************"""
    def __init__(self):
        r"""
        Init Method
        
        Initializes this class
        
        receives as argument the BeeConnection object ans veriffies the 
        connection status
        
        """
        
        self.findBEE()
        
        return

    """*************************************************************************
                            findBEE Method 

    *************************************************************************"""
    def findBEE(self):
        r"""
        findBE-E method
        
        searches for connected printers and tries to connect to the first one.
        """
        
        self.connected = False
        
        # find our device
        self.dev = usb.core.find(idVendor=0xffff, idProduct=0x014e,backend=libusb1.get_backend())
        #self.dev = usb.core.find(idVendor=0xffff, idProduct=0x014e,backend=libusb0.get_backend())
        #self.dev = usb.core.find(idVendor=0xffff, idProduct=0x014e,backend=openusb.get_backend())
        #self.dev = usb.core.find(idVendor=0xffff, idProduct=0x014e)
        
        if(self.dev is not None):
            print("BTF Old Connected")
        
        # was it found? no, try the other device
        if self.dev is None:
            self.dev = usb.core.find(idVendor=0x29c9, idProduct=0x0001,backend=libusb1.get_backend())
            if(self.dev is not None):
                print("BTF New Connected")
        if self.dev is None:
            self.dev = usb.core.find(idVendor=0x29c9, idProduct=0x0002,backend=libusb1.get_backend())
            if(self.dev is not None):
                print("BTF Plus Connected")
        if self.dev is None:
            self.dev = usb.core.find(idVendor=0x29c9, idProduct=0x0003,backend=libusb1.get_backend())
            if(self.dev is not None):
                print("BTF ME Connected")
        if self.dev is None:
            self.dev = usb.core.find(idVendor=0x29c9, idProduct=0x0004,backend=libusb1.get_backend())
            if(self.dev is not None):
                print("BTF School Connected")
        elif self.dev is None:
                raise ValueError('Device not found')

        if self.dev is None:
                print("Can't Find Printer")
                return
            
        # set the active configuration. With no arguments, the first
        # configuration will be the active one
        try:
            self.dev.set_configuration()
            self.dev.reset()
            time.sleep(0.5)
            #self.dev.set_configuration()
            self.cfg = self.dev.get_active_configuration()
            self.intf = self.cfg[(0,0)]
            print("reconnect")
        except usb.core.USBError as e:
            sys.exit("Could not set configuration: %s" % str(e))
        
        #self.endpoint = self.dev[0][(0,0)][0]

        self.ep_out = usb.util.find_descriptor(
                self.intf,
                # match the first OUT endpoint
                custom_match = \
                lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_OUT)

        self.ep_in = usb.util.find_descriptor(
                self.intf,
                # match the first in endpoint
                custom_match = \
                lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_IN)

        # Verify that the end points exist
        assert self.ep_out is not None
        assert self.ep_in is not None
        
        self.connected = True
        
        return
    
    """*************************************************************************
                            write Method

    *************************************************************************"""
    def write(self,message,timeout=500):
        r"""
        write method
        
        writes a message to the communication buffer
        
        arguments:
            message - data to be writen
            timeout - optional communication timeout (default = 500ms)
        
        returns:
            bytesWriten - bytes writen to the buffer
        """
        bytesWriten = 0
        
        if(message == "dummy"):
            pass
        else:
            try:
                bytesWriten = self.ep_out.write(message,timeout)
            except usb.core.USBError as e:
                return e
        
        return bytesWriten
    
    """*************************************************************************
                            read Method

    *************************************************************************"""
    def read(self,timeout=500, readLen=512):
        r"""
        read method
        
        reads existing data from the communication buffer
        
        arguments:
            timeout - optional communication timeout (default = 500ms)
            
        returns:
            sret - string with data read from the buffer
        """
     
        sret = ""
        
        try:
            self.write("")
            ret = self.ep_in.read(readLen, timeout)
            sret = ''.join([chr(x) for x in ret])
        except usb.core.USBError as e:
            if ("timed out" in str(e.args)):
                pass
            
        return sret
    
    """*************************************************************************
                            dispatch Method

    *************************************************************************"""
    def dispatch(self,message):
        r"""
        dispatch method
        
        writes data to the communication buffers and read existing data
        
        arguments:
            message - data to be writen
            
        returns:
            sret - string with data read from the buffer
        """
        
        timeout = self.READ_TIMEOUT
        
        if(message == "dummy"):
            pass
        else:
            time.sleep(0.009)
            self.ep_out.write(message)
            time.sleep(0.009)
        sret = ""
        
        try:
            ret = self.ep_in.read(self.DEFAULT_READ_LENGTH, timeout)
            sret = ''.join([chr(x) for x in ret])
        except usb.core.USBError as e:
            if ("timed out" in str(e.args)):
                pass
            
        return sret

    """*************************************************************************
                            sendCmd Method 

    *************************************************************************"""
    def sendCmd(self,cmd,wait=None,timeout=None):
        r"""
        sendCmd method
        
        sends command to the printer
        
        arguments:
            cmd - command to send
            wait - optional wait for reply
            timeout - optional communication timeout
        
        returns:
            resp - string with data read from the buffer
        """

        resp = None

        if wait is None:
            resp = self.dispatch(cmd)
        else:
            if(wait.isdigit()):
                resp = self.waitForStatus(cmd,wait,timeout)
            else:
                resp = self.waitFor(cmd,wait,timeout)
        
        return resp

    """*************************************************************************
                            waitFor Method 

    *************************************************************************"""
    def waitFor(self,cmd,s,timeout=None):
        r"""
        waitFor method
        
        writes command to the printer and waits for the response
        
        arguments:
            cmd - commmand to send
            s - string to be found in the response
            timeout - optional communication timeout
        
        returns:
            resp - string with data read from the buffer
        """
        
        self.write(cmd)
        
        resp = ""
        while(s not in resp):
            try:
                resp += self.read()
            except Exception:
                pass
        
        return resp

    """*************************************************************************
                            waitForStatus Method 

    *************************************************************************"""
    def waitForStatus(self,cmd,s,timeout=None):
        r"""
        waitForStatus method
        
        writes command to the printer and waits for status the response
        
        arguments:
            cmd - commmand to send
            s - string to be found in the response
            timeout - optional communication timeout
        
        returns:
            resp - string with data read from the buffer
        """
        
        self.write(cmd)
        
        str2find = "S:" + str(s)
        
        resp = ""
        while("ok" not in resp):
            try:
                resp += self.read()
            except Exception:
                pass
        
        while(str2find not in resp):
            try:
                self.write("M625\n")
                time.sleep(0.5)
                resp += self.read()
            except Exception:
                pass
        
        return resp


    """*************************************************************************
                            close Method

    *************************************************************************"""
    def close(self):
        r"""
        close method
        
        closes active connection with printer
        """
        try:
            # release the device
            usb.util.dispose_resources(self.dev)
            #usb.util.release_interface(self.dev, self.intf)    #not needed after dispose
        except:
            pass
        
        return
    
    
    """*************************************************************************
                            isConnected Method
    returns the connection state
    *************************************************************************"""
    def isConnected(self):
        r"""
        isConnected method
        
        returns the connection state
        
        returns:
            True if connected
            False if disconnected
        """
        
        return self.connected