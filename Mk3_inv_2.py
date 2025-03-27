import serial
import time
from serial.tools import list_ports
from serial.tools.list_ports import comports
from struct import *
from pymodbus.client.sync import ModbusTcpClient as ModbusClient

client = ModbusClient('localhost', port=5002)
client.connect()

#constants
mk2_addr = [0]*8
leds =[0]*8
adr_set = 0xff
b_Mk3 = False

def short_to_long(hi_byte,lo_byte):
    long_bytes = hi_byte*65536+lo_byte
    return(long_bytes)

def long_to_short(long_byes):
    temp = float(long_byes)
    hi_byte = int(temp/65536)
    lo_byte = int(temp-65536*hi_byte)
    #print("152",long_byes,hi_byte,lo_byte)
    return(hi_byte,lo_byte)

def long_to_vshort(long_byes):
    temp = long_byes
    hi_byte = temp >> 8
    lo_byte = int(temp-256*hi_byte)
    #print("152",long_byes,hi_byte,lo_byte)
    return(hi_byte,lo_byte)

def store_reg(mregisters,address):
    global client
    #return()
    slave_id = 0x01
    
    try:
        rq = client.write_registers(address, mregisters)
        
    except:
        print(46,"fail", address,mregisters)
        rq = -1
    return(rq)

def read_reg(nregisters,address):
    global client
    #return(-1)
    slave_id = 0x01
    try:
        f_resp = client.read_holding_registers(address,nregisters)
        f_data = f_resp.registers
        #print(77,f_data)
        return(f_data)
    except:
        return(-1)

def Find_Mk2():
    global com1,b_Mk3
    Mk2_port = ""
    com_ports_list = list(comports())
    for port in com_ports_list:
       # print(62,port[0],port[1])
        if port[1].startswith("MK2USB"):
            print("Mk2")
            Mk2_port = port[0] 
        if port[1].startswith("MK3-USB"):
            print("MK3")
            b_Mk3 = True
            Mk2_port = port[0] 
    if Mk2_port != "":
        com1 = serial.Serial( Mk2_port, baudrate=2400,parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS)
        return(Mk2_port)
    else:
        return(-1)

#Mk2 - OK 07 ff 56 98 3e 11 00 01 bc 07 ff 56 98 3e 11
#[4, 0, 0, 3, 0, 0, 0, 0]

def Mk2_Readstring():
    rxstring = ''
    while int(com1.inWaiting()) > 0:
            byte1 =(ord(com1.read(1)))
            rxstring +=("{:02x}".format(byte1))
            rxstring +=' ' 
    #print(28,rxstring)
    return(rxstring)

def Mk2_crc(xdata): 
    x=0
    for i in xdata:
        x +=i
        x = x % 0xff
        #print(x)
    crc = 0x100-x
    return(crc)

def Mk2_set_adr(adr):
    global adr_set
    initstring = bytes([0x04,0xff,0x41,0x01,adr,0xbb-adr]) # send "A, 1, Addr, checksum"
    com1.flushInput()
    com1.write(initstring)
    time.sleep(0.15)
    resp = Mk2_Readstring()
    #print(47,resp)
    adr_set = adr
    return()

def Mk2_Writestring(len,cmd,adr,sub,lsb=0,msb=0):
    global adr_set
    if adr_set != adr:
        Mk2_set_adr(adr)
    b_cmd = ord(cmd)
    print(56,"{:02x}".format(b_cmd))
    crc = Mk2_crc([len,0xFF,b_cmd,sub,lsb,msb])
    #print("{:02x}".format(crc))
    initstring = bytes([len,0xff,b_cmd,sub,lsb,msb,crc]) 
    print(59,initstring)
    com1.flushInput()
    com1.write(initstring)
    return()

def initMk2 ():
        
    print("Mk2 init")
   # V Version frame
    initstring = bytes([0x02,0xff,0x56,0xa9]) # Check for Mk 2 response  "V" 
    com1.flushInput()
    com1.write(initstring)
    time.sleep(0.5)
    rxstring = Mk2_Readstring()
    temp = rxstring.find('07 ff 56',0,len(rxstring)-1)   #listern for Mk2 id
    if temp == -1 :
        initMk2 = -1
        print("no Mk2")
        return(temp)
    else :  # discover devices
        print(" Mk2 - OK",rxstring)
        # A frame - set target address
        x = 0
        A = 0
        while x<3 or A <8: # limit 0x1F
            #print(87,A,x)
            Mk2_set_adr(A)
            #Mk2_Writestring(0x05,'W',A,0x0e) # get dev state
            initstring = bytes([0x05,0xff,0x57,0x0e,0x00,0x00,0x97]) # Check for device response 'W' 'e' = get device state
            com1.flushInput()
            com1.write(initstring)
            time.sleep(0.35)
            #print(89,com1.inWaiting())
            if com1.inWaiting() >0:
                f =Mk2_Readstring()
                temp = f.find('ff 57 94',0,len(f)-1)   #listern for Mk2 id
                if temp != -1:
                    f = f[temp:]
                    #print(97,f)
                    mk2_addr[A] = int(f[9:11]) # state of unit present at this index
                    print(158,mk2_addr[A])
                    x = 0
                    A+=1
                else:
                    x+=1
                    A+=1
            else:
                x+=1
                A+=1
        com1.flushInput()
        print(168,mk2_addr)
        return(mk2_addr)  

def LEDs(index):
    global com1,adr_set,leds
    
    Mk2_set_adr(index)
    time.sleep(0.1)
    initstring = bytes([0x02,0xff,0x4c,0xb3]) # L = 0x4c
    com1.flushInput()
    com1.write(initstring)
    time.sleep(0.52)
    resp = Mk2_Readstring()
    temp = resp.find('4c',0,len(resp)-1)   #listern for Mk2 id
    if temp != -1 :
        f = resp[temp:]
        #print(126,f,len(f))
        leds[index] = int(f[3:5],16) +256*int(f[6:8],16)
    #print(128,leds)
    return(leds)    
    
def get_ram_V_Inf(a,idx):
    Mk2_set_adr(a)
    time.sleep(0.1)
    initstring = bytes([0x05,0xff,0x57,0x36,0x05,0x00,0x6a]) # L = 0x4c
    com1.flushInput()
    com1.write(initstring)
    time.sleep(0.52)
    resp = Mk2_Readstring()
    print(198,resp)
    temp = resp.find('8e',0,len(resp)-1)   #listern for Mk2 id
    if temp != -1 :
        f = resp[temp:]
        #print(126,f,len(f))
        Sc = int(f[3:5],16) +256*int(f[6:8],16)
        if Sc >32768:
            print(205,Sc-0x8000)
            Sc = 1/(Sc-0x8000)
        print(206,Sc)
    else:
        Sc = -10
    return(Sc)
    
def Mk2_F(a,f_type):
    global com1,adr_set,mk2_addr
    f_data = [0]*9
    Mk2_set_adr(a)
    time.sleep(0.12)
    initstring = bytes([0x03,0xff,0x46,f_type,0xb8-f_type]) # L = 0x4c
    #print(144,initstring)
    com1.flushInput()
    com1.write(initstring)
    time.sleep(0.52)
    resp = Mk2_Readstring()
    temp = resp.find('20',0,len(resp)-1)   #listen for response
    if temp != -1 :
        f = resp[temp:]
       # print(204,a,f,len(f))
        
      # 204 0 20 02 02 00 04 08 00 00 00 00 cc 5b 72 00 ff 29  48
       # 0 ac [2, 0, 4, 0, 0, 23500, 114, 255, 0]
      
        # phase info f[]
        f_data[0] = int(f[3:5],16) #0
        #f_data[1] = int(f[6:8],16) #1; 2& 3 reserved
        f_data[1] = int(f[9:11],16) 
        f_data[2] = int(f[12:14])#4 Phase info
        f_data[3] = int(f[18:20],16) +256*int(f[21:23],16) #5,6 DC/Ac Volts
        if f_type == 0: #dc frame
            f_data[4] = int(f[24:26],16) +256*int(f[27:29],16)+65536*int(f[30:32],16) #7,8,9 inverter current
            f_data[5] =int(f[33:35],16) +256*int(f[36:38],16)+65536*int(f[39:41],16) #10,11,12 charger current
        else: # ac frame
            f_data[4] = int(f[24:26],16) +256*int(f[27:29],16) #7,8 mains current (ac)
            f_data[5] = int(f[30:32],16) +256*int(f[33:35],16) #9,10 inverter volt (ac)
            f_data[6] = int(f[36:38],16) +256*int(f[39:41],16) #11,12 inverter current
                   
        f_data[7] = int(f[42:44],16) #13 frequency data
        #print(223,a,f_type,f_data)
    return(f_data)               

def Mk3_H(h_state):  #?? Not documented?
    global com1,adr_set,mk2_addr
    initstring = bytes([0x03,0xff,0x48,h_state,0xb6-h_state]) # H = 0x48
    #print(144,initstring)
    com1.flushInput()
    com1.write(initstring)
    time.sleep(0.52)
    resp = Mk2_Readstring()
    print(227,resp)
    return(resp)
        
def Mk2_S(s_state): 
    global com1,adr_set,mk2_addr
    print(234,s_state)
    #return()
    Mk2_set_adr(0)  # always use master for switching off
    initstring = bytes([0x07,0xff,0x53,s_state,0x50,0x00,0x01,0x81,0xd5-s_state]) # S = 0x53
    #print(144,initstring)
    com1.flushInput()
    com1.write(initstring)
    time.sleep(0.42)
    resp = Mk2_Readstring()
    #print(218,resp)
    return(resp)

def Mk2_sw(a):
    Mk2_set_adr(a)
    initstring = bytes([ord('V')]) 
    #print(222,initstring)
    com1.flushInput()
    com1.write(initstring)
    time.sleep(0.5)
    resp1 = Mk2_Readstring()
    print("resp1",resp1)
   
    return()
    
def inv_sw(a):
    Mk2_set_adr(a)
    time.sleep(0.1)
    initstring = bytes([0x05,0xff,0x57,0x05,0x00,0x00,0xa0]) 
    #print(222,initstring)
    com1.flushInput()
    com1.write(initstring)
    time.sleep(0.5)
    resp1 = Mk2_Readstring()
    print("inv resp1",resp1)
    initstring = bytes([0x05,0xff,0x57,0x06,0x00,0x00,0x9f]) 
    #print(222,initstring)
    com1.flushInput()
    com1.write(initstring)
    time.sleep(0.5)
    resp2 = Mk2_Readstring()
    print("inv resp2",resp2)
    return()

def Mk2_rdRamVar_1(a=0,adr=80):
    Mk2_set_adr(a)
    time.sleep(0.1)
    wt_str = bytes([0x05,0xFF,0x57,0x30,adr,0x00,0x175-adr])
    com1.flushInput()
    com1.write(wt_str)
    time.sleep(0.42)
    resp = Mk2_Readstring()
    #print(313,resp)
    xasit =0 # resp[-1]
    return(xasit)

def Mk2_wrt_RamVar(adr,p,a=0):
    Mk2_set_adr(a)
    time.sleep(0.1)
    wt_str = bytes([0x05,0xFF,0x57,0x32,adr,0x00,0x173-adr])
    com1.flushInput()
    com1.write(wt_str)
    if p < 0:
        p = 65536+p 
    #print(325,p)
    if p > 255:
        ph,pl = long_to_vshort(p)
    else:
        ph = 0
        pl = p
   # print(328, pl,ph,p)
    wt_str = bytes([0x05,0xFF,0x57,0x34,pl,ph,(0x271-pl-ph)&0xff])
    com1.flushInput()
    com1.write(wt_str)
    time.sleep(0.42)
    resp = Mk2_Readstring()
    print(333,resp)
    return()

time.sleep(5) #wait for other program to setup and run
Find_Mk2()
inv = initMk2()  # from here code needs to be adapted for multiple inverters...
for a,s in enumerate(inv):
    if s !=0:
        store_reg(s,599+10*a) # store mode in
        #Mk2_sw()  # why - already done, & Mk2 version not used.
        inv_sw(a)
        LEDs(a)
        Sc = get_ram_V_Inf(0,5)
        Mk2_S(2)
    # if b_Mk3:
    #     Mk3_H(0)

cnt = 0
while True:
    for a,s in enumerate(inv):
        if s >2:
            dc_frame = Mk2_F(a,0)
            try:
                print(a,"dc",dc_frame)
                 #0 dc [109, 161, 1, 5296, 2.25, 0.0, 0, 135, 0]
                store_reg(dc_frame[3],592+10*a) # dc volt
                store_reg(dc_frame[4],593+10*a) # inverter amp
                store_reg(dc_frame[4],603+10*a) # inverter amp
                store_reg(dc_frame[5],594+10*a) # charger amp
                store_reg(dc_frame[7],595+10*a) # freq
            except Exception as e:
                print(299,e)
        
            ac_frame = Mk2_F(a,1)
            try:
                #0 ac [2, 2, 8, 0, 0, 23500, 115, 255, 0]
                #3 ac [2, 2, 8, 0, 0, 23500, 126, 255, 0]
                print(a,"ac",ac_frame)
                store_reg(ac_frame[5],590+10*a)
                if ac_frame[6] > 32768:
                    aca = ac_frame[6]-65536
                else:
                    aca = ac_frame[6]
                store_reg(aca,591+10*a)  # inverter current, signed
                store_reg(ac_frame[7],596+10*a)
                store_reg(ac_frame[3],597+10*a)

                store_reg(ac_frame[4],598+10*a)
            except Exception as e:
                print(310,e)
            f=LEDs(a)[0]
            print(390,"leds",f)
            store_reg(f,600)
            f= Mk2_rdRamVar_1(a,0x82)
            f= Mk2_rdRamVar_1(a,0x83)
            f= Mk2_rdRamVar_1(a,0x84)
            #f= Mk2_rdRamVar_1(a,0x85)
            #f= Mk2_rdRamVar_1(a,0x86)
           # Mk2_wrt_RamVar(0x85,0,0)
           # Mk2_wrt_RamVar(0x84,1,0)
            Mk2_wrt_RamVar(0x83,0,0)
           #Mk2_wrt_RamVar(0x87,100,0)
            time.sleep(0.5)
