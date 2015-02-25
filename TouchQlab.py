import os
import json
import datetime
from decimal import Decimal
try:
    from OSC import *
except ImportError:
    FullExit()



ReplyIP = "127.0.0.1"
ReplyPort = 53001
SendIP = None#"10.3.3.254"#None
SendPort = 54001
WorkspaceID = None
valuesForKeys = ""
sliderLevels = ""

def SendMessage(addr, message, client):
    try:
        if (message == None):
            client.send( OSCMessage(addr ) )
        else:
            client.send( OSCMessage(addr, message) )
    except Exception, e:
        print str(e)
qlabClient = None
def SendQLabMessage(addr, message):
    global qlabClient
    if (qlabClient is None):
        qlabClient = OSCClient()
        clientAddress = ( "127.0.0.1", 53000 )
        qlabClient.connect(clientAddress)
    SendMessage(addr, message, qlabClient)
deviceClient = None
def SendDeviceMessage(addr, message):
    global deviceClient
    global SendIP
    global SendPort
    if (deviceClient is None):
        deviceClient = OSCClient()
        clientAddress = ( SendIP, SendPort )
        deviceClient.connect(clientAddress)

    if ("displayName" in addr):
        print addr + " " + message
        print deviceClient
    SendMessage(addr, message, deviceClient)

    
def SendBundle(OSCMessages, client):
    try:
        if (message == None):
            client.send( OSCBundle(addr ) )
        else:
            client.send( OSCBundle(addr, message) )
    except Exception, e:
        print str(e)
def SendQLabBundle(OSCMessages):
    global qlabClient
    if (qlabClient is None):
        qlabClient = OSCClient()
        clientAddress = ( "127.0.0.1", 53000 )
        qlabClient.connect(clientAddress)
    SendBundle(OSCMessages, qlabClient)
deviceClient = None
def SendDeviceBundle(OSCMessages):
    global deviceClient
    global SendIP
    global SendPort
    if (deviceClient is None):
        deviceClient = OSCClient()
        clientAddress = ( SendIP, SendPort )
        deviceClient.connect(clientAddress)
    SendBundle(OSCMessages, deviceClient)



def Exit_Handler(addr, tags, data, source):
    FullExit()
    
#--------------------------------------------------------------------------------
def SecondsToString(sec):
    sec = round(sec, 2)
    returnString = str(sec - int(sec)).replace("0.", "")
    returnString = time.strftime("%M:%S:", time.gmtime(sec)) + returnString
    return returnString
#--------------------------------------------------------------------------------
def RequestValuesForKeys():
    if (SendIP is not None):
        SendQLabMessage("/cue/selected/valuesForKeys", "[\"displayName\",\"number\", \"type\", \"isBroken\", \"isLoaded\", \"isPaused\", \"isRunning\", \"preWait\", \"duration\", \"postWait\", \"translationX\", \"translationY\", \"opacity\",\"scaleX\",\"scaleY\"]")
        SendQLabMessage("/cue/selected/sliderLevels", None) 
#--------------------------------------------------------------------------------
def Server_handler(addr, tags, data, source):
    global SendIP
    global WorkspaceID
    if (WorkspaceID is None):
        return
    if  (str(source[0]) == "127.0.0.1"): #From Qlab
        if (TouchOSCIP != None):
            print "Received a message from Qlab, but nothing is wired up yet"
    else: #From Other Device
        if (SendIP == None):
            SendIP = source[0]
            
        if ("{WorkspaceID}" in addr):
            addr = addr.replace("{WorkspaceID}", WorkspaceID)

        if ("/page/" in addr):
            RequestValuesForKeys()
            print 'Page Changed'
        elif (("/previous" in addr) or
            ("/next" in addr) or
            ("/save" in addr) or
            ("/undo" in addr) or
            ("/redo" in addr) or
            ("/load" in addr and "/loadAt" not in addr) or
            ("/go" in addr) or
            ("/panic" in addr) or
            ("/hardStop" in addr) or
            ("/start" in addr) or
            ("/stop" in addr) or
            ("/pause" in addr) or
            ("/resume" in addr) or
            ("/reset" in addr) or
            ("/selected/stop" in addr)):
            if (data[0] == 1.0): #Button press down only
                SendQLabMessage(addr, None)
        elif ("sliderLevel" in addr):
            if ("+" in addr or "-" in addr):
                if (data[0] > 0):
                    print addr + " " + str(data[0])
                    SendQLabMessage(addr, data[0])
            else:
                db = float(data[0])
                db = db * 72 - 62
                SendQLabMessage(addr, db)
        elif (len(data) == 0):
            SendQLabMessage(addr, None)
        elif (len(data) == 1):
            print addr
            SendQLabMessage(addr, data[0])
        elif (len(data) == 2):
            print addr
            if ("/translation" in addr):
                SendQLabMessage(addr.replace("/translation", "/translationX"), data[0])
                SendQLabMessage(addr.replace("/translation", "/translationY"), data[1])
                
        else:
            print str(data)
#--------------------------------------------------------------------------------

        
#--------------------------------------------------------------------------------
def Listener_handler(addr, tags, data, source):
    global WorkspaceID
    global valuesForKeys
    global sliderLevels
    #print data
    #print addr
    if ("/update/workspace" in addr):
        print "Update Received"
        RequestValuesForKeys()
    elif (len(data) > 0 and "data" in data[0]):
        #parse out the data portion of the JSON string
        strData = data[0]
        decodedJson = json.loads(strData)
        if ("/reply/workspaces" in addr):
            WorkspaceID = decodedJson['data'][0]['uniqueID']
            print WorkspaceID
            SendQLabMessage("/workspace/" + WorkspaceID + "/updates", 1)
        elif ("/reply" in addr and "/thump" in addr):
            print "thump thump"
        elif ("/valuesForKeys" in addr):
            strData = decodedJson['data']
            if (strData != valuesForKeys): #Then there have been changes
                valuesForKeys = strData
                #print valuesForKeys
                SendDeviceMessage("/cue/selected/displayName", str(decodedJson['data']['displayName']))
                SendDeviceMessage("/cue/selected/number", "#" + str(decodedJson['data']['number']))
                SendDeviceMessage("/cue/selected/type", "Cue Type: " + str(decodedJson['data']['type']))
                
                SendDeviceMessage("/cue/selected/isBroken", (1 if decodedJson['data']['isBroken'] else 0))
                SendDeviceMessage("/cue/selected/isLoaded", (1 if decodedJson['data']['isLoaded'] else 0))
                SendDeviceMessage("/cue/selected/isRunning", (1 if decodedJson['data']['isRunning'] else 0))
                SendDeviceMessage("/cue/selected/isPaused", (1 if decodedJson['data']['isPaused'] else 0))
                
                SendDeviceMessage("/cue/selected/preWait", decodedJson['data']['preWait'])
                SendDeviceMessage("/cue/selected/preWait/string", SecondsToString(decodedJson['data']['preWait']))
                SendDeviceMessage("/cue/selected/duration", decodedJson['data']['duration'])
                SendDeviceMessage("/cue/selected/duration/string", SecondsToString(decodedJson['data']['duration']))
                SendDeviceMessage("/cue/selected/postWait", decodedJson['data']['postWait'])
                SendDeviceMessage("/cue/selected/postWait/string", SecondsToString(decodedJson['data']['postWait']))

                if ("opacity" in decodedJson['data']):
                    SendDeviceMessage("/cue/selected/opacity", decodedJson['data']['opacity'])
                    SendDeviceMessage("/cue/selected/opacity/string", round(decodedJson['data']['opacity']*100, 0))
                if ("scaleX" in decodedJson['data']):
                    SendDeviceMessage("/cue/selected/scaleX", decodedJson['data']['scaleX'])
                    SendDeviceMessage("/cue/selected/scaleX/string", round(decodedJson['data']['scaleX'], 2))
                if ("scaleY" in decodedJson['data']):
                    SendDeviceMessage("/cue/selected/scaleY", decodedJson['data']['scaleY'])
                    SendDeviceMessage("/cue/selected/scaleY/string", round(decodedJson['data']['scaleY'], 2))
                if ("translationX" in decodedJson['data']):
                    SendDeviceMessage("/cue/selected/translation", (decodedJson['data']['translationX'],decodedJson['data']['translationY']))
                    SendDeviceMessage("/cue/selected/translationX/string", round(decodedJson['data']['translationX'], 2))
                    SendDeviceMessage("/cue/selected/translationY/string", round(decodedJson['data']['translationY'], 2))
        elif ("/sliderLevels" in addr):
            strData = decodedJson['data']
            if (strData != sliderLevels): #Then there have been changes
                sliderLevels = strDatamessages = []
                for x in range (0, 9):
                    dB = (float(decodedJson['data'][x]) + 60) / 72
                    SendDeviceMessage( "/cue/selected/sliderLevel/" + str(x), dB) 
                    SendDeviceMessage( "/cue/selected/sliderLevel/" + str(x) + "/string", str(round(decodedJson['data'][x], 1)) + "dB")
        else:
            print "Method not implemented: " + addr + "\n" + str(decodedJson)
            
    elif (len(data) > 0):
        if ("/cue/selected/name" in addr):
            SendQLabMessage(addr, data[0])
            
    else:
        SendQLabMessage(addr, "")
#--------------------------------------------------------------------------------






try:
    import logging
    import socket
    import time, threading
    from subprocess import Popen, PIPE
    import telnetlib
except ImportError:
    print "Import Error: Missing Python Library\n\n" + e
    os._exit(0) 


try:
    srvr = OSCServer( ('0.0.0.0', 54000) )
    srvr.addMsgHandler("default", Server_handler)
    srvr.addMsgHandler("/quit", Exit_Handler)
    srvr.addMsgHandler("/exit", Exit_Handler)

    lstnr = OSCServer( ('127.0.0.1', 53001) )
    lstnr.addMsgHandler("default", Listener_handler)

except Exception, e:
    print "There was an error opening the socket.\nThis may simply be because another app is using port 54000.\nIf the problem persists, please restart your computer and try again.\n\n" + str(e)
    FullExit()


    

    


# Start OSCServers
print "\nStarting OSCServer. Use ctrl-C to quit."
SendThread = threading.Thread( target = srvr.serve_forever )
SendThread.start()

ReplyThread = threading.Thread( target = lstnr.serve_forever )
ReplyThread.start()


DoPing = True

def FullExit() :
    print "\nWaiting for Server-threads to finish"

    print "\nClosing Ping Thread"
    DoPing = False
    
    print "\nClosing Server."
    srvr.close()
    SendThread.join() ##!!!
    
    print "\nClosing Listener"
    lstnr.close()
    ReplyThread.join()
    
    
    print "Done"

    os._exit(0)

try :
    while DoPing:
        if (WorkspaceID == None):
            SendQLabMessage("/workspaces", None)
            time.sleep(1)
        else:
            if (SendIP == None):
                time.sleep(1)
            else:
                try:
                    SendQLabMessage("/workspace/" + WorkspaceID + "/thump", None)
                    time.sleep(20)
                except Exception, e:
                    print "There was an exception\n" + str(e)
                    WorkspaceID = None
                    SendIP = None
            
except KeyboardInterrupt :
    FullExit()
