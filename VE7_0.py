#pi@raspberrypi:~ $ sudo date -s"Feb 10 11:25 2018"
#Saturday 10 February  11:25:00 FJT 2018
 
from struct import *
from time import *
import time  
import serial
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from serial.tools import list_ports
from serial.tools.list_ports import comports
#constants
mppt = 0
sms = 1
dev_list = [2]*5
max_list = [0]*5
#MPPT / Blue / Smart Solar
msg_get_AbsV  =str.encode( ":7F7ED006A"+chr(0x0a))
msg_get_BmaxA =str.encode( ":7F0ED0071"+chr(0x0a))
msg_get_CmaxA =str.encode( ":7DFED0082"+chr(0x0a))
msg_get_tyld =str.encode( ":7DDED0084"+chr(0x0a))
msg_get_tmp =str.encode( ":7DBED0086"+chr(0x0a))
msg_get_err =str.encode( ":7F0ED0087"+chr(0x0a))
msg_get_champ =str.encode( ":7D7ED008A"+chr(0x0a))
msg_get_chvlt =str.encode( ":7D5ED008C"+chr(0x0a))
msg_get_iyld =str.encode( ":7D3ED008E"+chr(0x0a))
msg_get_imxp =str.encode( ":7D2ED008F"+chr(0x0a))
msg_get_pvmp =str.encode( ":7BCED00A5"+chr(0x0a))
msg_get_pviv =str.encode( ":7BBED00A6"+chr(0x0a))
msg_get_pid = str.encode(":70001004D"+chr(0x0a)) # com
msg_get_intt = str.encode(":7DBED0086"+chr(0x0a))
msg_get_devs = str.encode(":70C200022"+chr(0x0a))
msg_get_trcm = str.encode(":7B3ED00AE"+chr(0x0a))
msg_get_dyyd = str.encode(":7D1ED0090"+chr(0x0a))
msg_get_mpyd = str.encode(":7D0ED0091"+chr(0x0a))
msg_ping = str.encode( ':154'+chr(0x0a))
msg_set_ubat = str.encode(":8F1ED00FF70"+chr(0xa))
msg_set_tbatc = str.encode(":8F2ED00006E"+chr(0xa))
msg_set_vbata = str.encode(":8F7ED00040B5A"+chr(0xa))#":8F7ED00C80A97" inc from 27.6 to 28V
msg_set_vbatf = str.encode(":8F6ED00030B5C"+chr(0xa))
msg_set_eqoff = str.encode(":8FDED000063"+chr(0xa))
msg_set_tabs = str.encode(":8FBED009001D4"+chr(0xa))
msg_set_vbate = str.encode(":8F4ED00180B49"+chr(0xa))
msg_set_Ibatm = str.encode(":8F0ED00BC02B2"+chr(0xa))
msg_set_nBMS = str.encode(":8E8ED000078"+chr(0xa))
msg_set_extm = str.encode(":80E2000021D"+chr(0xa))
msg_set_extI = str.encode(":8152000DC0537"+chr(0xa))
msg_restart = str.encode(":64F"+chr(0xa))

# Smart Shunt
msg_get_subat0 = str.encode( ":78DED00D4"+chr(0x0a))
msg_get_subat1 = str.encode( ":77DED00E4"+chr(0x0a))
msg_get_sIbat0 = str.encode( ":78FED00D2"+chr(0x0a))
msg_get_sIbat_hr = str.encode( ":78CED00D5"+chr(0x0a))
msg_get_sSOC = str.encode( ":7FF0F0040"+chr(0x0a))
msg_get_spwr = str.encode( ":78EED00D3"+chr(0x0a))
msg_get_ddd =  str.encode( ":70003004B"+chr(0x0a))
msg_get_dld =  str.encode( ":70103004A"+chr(0x0a))
msg_get_dad =  str.encode( ":702030049"+chr(0x0a))

reg_dict = { # Note all VE registers are byte swapped!!!
    0x0001 : [770,32],   #PID
    0x0C20 : [778, 8],  # device state
    0x0202 : [779, 32],    # remote used
    0x0220 : [788,16],   #remote v batt
    #0xFBED : [777, 16],    # Abs time limit
    #0xF7ED : [776, 16] ,   # Abs voltage
    #0xF6ED : [775, 16],    #float volt
    0xDFED : [792, 16],  # max current
    0xDDED : [783, 32],  #System Yield
    0xDBED : [775, 15],  # internal temp (signed)
    0xDAED : [782, 8],   #error
    0xD7ED : [772, 16],  #charge current
    0xD5ED : [771, 16], # batt voltage
    
    0xD3ED : [773, 16],  # today yeild
    0xD2ED : [785, 16],  # max power day
    0xD1ED : [786, 16],  # yeild yesterd
    0xD0ED : [787, 16],  # max p -24h
    0xBBED : [776, 16], #pv volt
    0xBCED : [789, 32], # pv power
    0xB3ED : [777, 8],   #tracker mode
    0x1520 : [793, 16],  #charge limit
    0xF1ED : [800,16],
    0xF2ED : [808,16], # temp comp
    0xF7ED : [801,16],
    0xFDED : [802,16],
    0xFBED : [803,16],
    0xF4ED : [804,16],
    0xE8ED : [805,16],
    0xF0ED : [806,16]
    #0xD1ED : [786, 16], #Yield -24h
    #0xD0ED : [787, 16] #Max P -24h
}
reg_dict_sh={
    0x0001 : [870,32],   #PID
    0x8DED : [871,16], #main bat volt
    0x7DED : [872,16], #aux bat volt
    0x8FED : [873,16], # current
    0x8CED : [874,32], # HR current
    0x0FFF : [876,16], #SOC
    0x8EED : [877,16],  #pwr
    0x0003 : [878,32], # deep discharge
    0x0103 : [880,32], #last discharge
    0x0203 : [882,32]  # average discharge
    }
com = ["null"]*5
pid = [0]*5
CmaxA = [0]*5
champ = [0]*5
chvlt = [0]*5
pvv = [0]*5
pvy  = [0]*5
pvmp = [0]*5
tyld = [0]*5
mptemp=[0]*5
devs = [0]*5
trcm = [0]*5
pvmxp = [0]*5
dyyd = [0]*5
mpydd = [0]*5

#VE Direct
def Find_VED():
    VED_port = ["null"]*5
    com_ports_list = list(comports())
    
    for i,port in enumerate(com_ports_list):
        if port[1].startswith("VE Direct"):
            VED_port[i] = port[0]  
    return(VED_port)
    
def dec2hex_str(dd1):
    hi_by = int(dd1/256)
    lo_by = dd1-hi_by*256
    #print(54,"{:04X}".format(dd1),"{:02X}".format(hi_by),"{:02X}".format(lo_by))
    I_str = ("{:02X}".format(lo_by))+("{:02X}".format(hi_by))
    msg_set_Imax = "8152000"+I_str
    chk = 0x118 -lo_by-hi_by
    #print(58,"check","{:02x}".format(chk))
    chk = chk%256
    st_ch =("{:02X}".format(chk))
    msg_set_Imax += st_ch
    b_msg_Imax = str.encode(":"+msg_set_Imax+chr(0x0a))
    return(b_msg_Imax)

def dec2hex_Vstr(dd1):
    hi_by = int(dd1/256)
    lo_by = dd1-hi_by*256
    #print(54,"{:04X}".format(dd1),"{:02X}".format(hi_by),"{:02X}".format(lo_by))
    V_str = ("{:02X}".format(lo_by))+("{:02X}".format(hi_by))
    msg_set_v = "8022000"+V_str
    chk = 0x12B -lo_by-hi_by
    #print(58,"check","{:02x}".format(chk))
    chk = chk%256
    st_ch =("{:02X}".format(chk))
    msg_set_v += st_ch
    b_msg_v = str.encode(":"+msg_set_v+chr(0x0a))
    return(b_msg_v)    

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
    temp = float(long_byes)
    hi_byte = int(temp/256)
    lo_byte = int(temp-256*hi_byte)
    #print("152",long_byes,hi_byte,lo_byte)
    return(hi_byte,lo_byte)

def store_reg(mregisters,address):
    global client
    
    slave_id = 0x01
    if address == 789:
        print(135,"pvp",mregisters)
    try:
        rq = client.write_registers(address, mregisters)
    except:
        rq = -1
    return(rq)

def read_reg(nregisters,address):
    global client
    slave_id = 0x01
    
    #print(106,address,f_registers)
    #f_data = context[slave_id].getValues(register,address, f_registers)
    f_resp = client.read_holding_registers(address,nregisters)
    f_data = f_resp.registers
    #print(77,f_data)
    return(f_data)

def read_float(addr):
    global client
    val_lst = [0,0,0,0]
    slave_id = 0x01
    try:
        f_resp = client.read_holding_registers(addr,2)
        f_data = f_resp.registers
    except:
        f_data = [0,0]
    val_lst[0],val_lst[1] = long_to_vshort(f_data[0])
    val_lst[2],val_lst[3] = long_to_vshort(f_data[1])
    val_bytes = bytes(val_lst)
    val_t = unpack('f',val_bytes)
    val = val_t[0]
    return(val)
    
def sumx(templst = []):
    global dev_list
    tval = 0
    #print(220,templst)
    for i,val in enumerate(templst):
        if dev_list[i] == 0:
            if int(val) > 0:
                tval += val
    return(tval)
    
def avgx(templst = []):
    global dev_list
    tval = 0
    mcnt =0
    for i,val in enumerate(templst):
        if dev_list[i] == 0:
            if int(val) > 0:
                tval += val
                mcnt +=1
    return(tval/mcnt)    
    
def maxx(templst = []):
    global dev_list
    tval = 0
    for i,val in enumerate(templst):
        if dev_list[i] == 0:
            if int(val) > 0:
                if tval <= val:
                    tval = val
    return(tval)    

def read_hex(i):
    global com
    pid[i] = write_VE(i,msg_get_pid)
    pid[i] = write_VE(i,msg_get_pid)
    if int(pid[i]) >0:
        #print(154,i,"PID","{:04x}".format(pid[i]))
        store_reg([pid[i]],770+20*i)
    
    # CmaxA[i] = write_VE(i,msg_get_CmaxA) # not used
    # print(156,i,"Ch Mx A",CmaxA[i])
    # store_reg([CmaxA[i]],792+20*i)
    
    champ[i] = write_VE(i,msg_get_champ)
    #if val > 700:
     #   val = 699
    if int(champ[i])  > 0:
        #print(258,i,champ[i])
        store_reg([sumx(champ)],772)
        print(158,i,"bat I",sumx(champ),champ)
    
    chvlt[i] = write_VE(i,msg_get_chvlt)
    if int(chvlt[i]) > 0 :
        print(265,i,"Charge Volt",chvlt[i]/100)
        store_reg([avgx(chvlt)],771)
       # print(160,i,"bat V",avgx(chvlt),chvlt)
    
    pvv[i] = write_VE(i,msg_get_pviv) # once mppt saturates output current, PV voltage rises.
    if int(pvv[i]) > 0:
        store_reg([avgx(pvv)],776)      # average function won't indicate the higherst pvv.
      #  print(162,i,"PV V",avgx(pvv),pvv)
    
    pvy[i] = write_VE(i,msg_get_iyld)
    if int(pvy[i])>0:
        store_reg([sumx(pvy)],773)
      #  print(164,i,"PV Yld",sumx(pvy),pvy)
    
    pvmp[i] = write_VE(i,msg_get_pvmp)
    if int(pvmp[i]) >0:
        hpvp,lpvp = long_to_short(sumx(pvmp))
        store_reg([lpvp,hpvp],789)
    #    print(166,i,"PV  Pmx",sumx(pvmp),pvmp)
    
    tyld[i] = write_VE(i,msg_get_tyld)
    if int(tyld[i]) > 0:
        htyld,ltyld = long_to_short( sumx(tyld))
        if htyld>0xffff or ltyld > 0xffff:
            print(294,"OOPS!")
        store_reg([ltyld,htyld],783) 
      #  print(168,i,"PV tot yld", sumx(tyld),tyld)
    
    mptemp[i] = write_VE(i,msg_get_tmp) #need max function
    if int(mptemp[i]) > 0:
        store_reg([maxx(mptemp)],775)
        print(170,i,"int temp",maxx(mptemp),mptemp)
    
    devs[i] = write_VE(i,msg_get_devs) # this should track for all devs.
    if int(devs[i]) > 0:
        store_reg([devs[i]],778+20*i)
        print(172,i,"dev state",devs[i],devs)
    
    trcm[i] = write_VE(i,msg_get_trcm)
    if int(trcm[i]) > 0:
        trcm[i] &= 0x03
        store_reg([trcm[i]],777+20*i)
        print(174,i,"track mode",trcm[i],trcm)
    
    pvmxp[i] = write_VE(i,msg_get_imxp) #long to short?
    if int(pvmxp[i]) >0:
        store_reg([sumx(pvmxp)],785)
        print(176,i,"PV max P",sumx(pvmxp))
    
    dyyd[i] = write_VE(i,msg_get_dyyd)
    if int(dyyd[i])>0:
        store_reg([sumx(dyyd)],786)
     #   print(178,i,"PV -24h yield",sumx(dyyd),dyyd)
    
    # mpydd[i] = write_VE(i,msg_get_mpyd)
    # if int(mpydd[i])>0:
    #     store_reg([sumx(mpydd)],787)
    #     print(180,i,"PV mpyd",sumx(mpydd),mpydd)
    return()
    
def read_hex_s(i):
    val = write_VE(i,msg_get_pid)
    val = write_VE(i,msg_get_pid)
    if int(val) >0:
        print(254,i,"PID","{:04x}".format(int(val)))
        store_reg([val],870)
    val = write_VE(i,msg_get_subat0)
    if int(val) >0:
        print(256,i,"V Batt","{:04x}".format(int(val)))
        store_reg([val],871)
    val = write_VE(i,msg_get_subat1)
    if int(val) >0:
        print(259,i,"V Aux","{:04x}".format(int(val)))
        store_reg([val],872)
    val = write_VE(i,msg_get_sIbat0)
    if int(val) >0:
        print(264,i,"Ibat ","{:04x}".format(val))
        store_reg([val],873)
    val = write_VE(i,msg_get_sIbat_hr)
    if int(val) >0:
        print(266,i,"Ibat HR","{:04x}".format(val))
        htyld,ltyld = long_to_short(val)
        store_reg([ltyld,htyld],874) 
    val = write_VE(i,msg_get_sSOC)
    if int(val) >0:
        print(268,i,"SOC","{:04x}".format(val))
        store_reg([val],876)
    val = write_VE(i,msg_get_spwr)
    if int(val) >0:
        print(268,i,"PWR","{:04x}".format(val))
        store_reg([val],877)
    # val = write_VE(i,msg_get_ddd)
    # if int(val) >0:
    #     print(285,i,"DDD","{:04x}".format(val))
    # val = write_VE(i,msg_get_dld)
    # if int(val) >0:
    #     print(287,i,"dld","{:04x}".format(val))
    # val = write_VE(i,msg_get_dad)
    # if int(val) >0:
    #     print(289,i,"dad","{:04x}".format(val))
    
    return()

def read_msg(i):
    rxstring = ""
    #print(242,com2.in_waiting)
    a = False
    c = 0
    try:
        while a==False or c<18: #int(com[i].inWaiting()) > 0:

            byte1 =ord(com[i].read(1))
            if byte1 == 0x0a:
                a = True
            rxstring +=(chr(byte1))
            c +=1
    except Exception as e:
        print(355,e)
        com[i].flush()
        return(":\n")
    return(rxstring)    

def dec_rx_msg(i,reg,xdata):
    global reg_dict,mppt,sms
    #print(363,i,reg,xdata)
    if dev_list[i] == 0:
        try:
            rg = reg_dict[int(reg,16)]
        # print(366,i,rg,reg,xdata)
        except:
            print(367,"dict fail",i,int(reg,16),"{:04x}".format(xdata))
            store_reg([reg],794)
            return(-1)
    else:
        try:
            rg = reg_dict_sh[int(reg,16)]
        except:
            print(374,"dict fail",i,int(reg,16),"{:04x}".format(xdata))
            store_reg([reg],894)
            return(-1)
    if rg[1]== 8:
        xdata = xdata&0xff
        store_reg([xdata],rg[0])
    if rg[1] == 16 or rg[1] == 15:
        store_reg([xdata],rg[0])
    if rg[1] == 32 and xdata <= 0xffff:
        store_reg([xdata&0xffff],rg[0])
    if rg[1] == 32 and xdata > 0xffff:
        # should be store float..
        store_reg([xdata&0xffff],rg[0])
        store_reg([xdata>>16],rg[0]+1)

    return(1)

def write_VE(i,msg):
    global com
    if com[i] == "null":
        print(394,i,com[i],msg)
        return(-1)
    time.sleep(0.1)
    rx_str = ""
    val_str = ""
    #print(330,i,msg)
    try:
        com[i].flush()
    except Exception as e:
        print(399,i,e)
        print(401,com[i])
        #com[i].readall
    f = com[i].in_waiting
    if msg == msg_restart:
        return
    if f >  0:
        time.sleep(0.5)
        try:
            com[i].reset_input_buffer()
        except Exception as e:
            print(359,e)
    b = com[i].write(msg)
    #print(256,msg, b)
    f=0
    while f < 6:
        f = com[i].in_waiting
    #print(362,f)
    if f > 0 :
        rx_str = read_msg(i)
        nl = rx_str.find(":") 
        el = rx_str.find("\n")
        rs_str = rx_str[nl:el] 
        if nl != 0:
            #print(427,"rxstring short",nl,f,rx_str)
            return("-2")
        #print("\n","\n",382,nl,len(rx_str),len(rs_str),ord(rs_str[0:1]))
        flags = rx_str[6:8]
        reg = rx_str[2:6]
        val_str = rx_str[8:-3]
        if len(val_str) ==7:
            val_str = val_str[0:4]
        if str(flags) !="00":
            print(372,reg,flags,len(val_str),val_str,rs_str)
    if len(val_str) == 4:
        big_val_str = val_str[2:4]+val_str[0:2] #swap bytes
        try:
            val = int(big_val_str,16)
            #
        except:
            print(493,i,reg,big_val_str,msg)
            time.sleep(0.5)
            return(-3)
        dec_rx_msg(i,reg,val)
    elif len(val_str) == 2:
        val = int(val_str)
        #print(420,i,reg,val)
        dec_rx_msg(i,reg,val)
    elif len(val_str) == 8 and reg == "0001":
        big_val_str = val_str[4:6]+val_str[2:4] #swap bytes
        val = int(big_val_str,16)
        #print(425,i,reg,val)
        dec_rx_msg(i,reg,val)
    elif len(val_str) == 8 and reg != "0001":
        big_val_str = val_str[6:8]+val_str[4:6]+val_str[2:4]+val_str[0:2] #swap bytes
        val = int(big_val_str,16)
        #print(430,i,reg,val)
        dec_rx_msg(i,reg,val)
    else:
        print(377,i,msg,rs_str,val_str)
        val = -1  
    
    return(val)

def Set_MPPT(i):
    write_VE(i,msg_restart)
    time.sleep(2)
    f = write_VE(i,msg_set_ubat)
    print(375,f)
    f = write_VE(i,msg_set_tbatc)
    print(377,f)
    f = write_VE(i,msg_set_vbata)
    print(379,f)
    f = write_VE(i,msg_set_vbatf)
    print(381,f)
    f = write_VE(i,msg_set_eqoff)
    print(383,f)
    f = write_VE(i,msg_set_tabs)
    print(385,f)
    f = write_VE(i,msg_set_vbate)
    print(387,f)
    f = write_VE(i,msg_set_Ibatm)
    print(389,f)
    f = write_VE(i,msg_set_nBMS)
    print(391,f)
    f = write_VE(i,msg_set_extm)
    print(393,f)
    f = write_VE(i,msg_set_extI)
    print(395,f)
    return()

def getImax(i):
    global com
    val = -1
    while int(val) < 0:
        val = write_VE(i,msg_get_BmaxA)
    
    print(554,"Bmax A",val)
    
    if val < 70:
        Val = 70
    return(val)

def get_params(i):
    
    # Float Voltage
    # Bat max amps
    write_VE(i,msg_ping) # shut the ascii mode up!!
    f = write_VE(i,msg_set_Ibatm)
    print(566,f)
    val = getImax(i)
    I_max_set = val
    store_reg([val],792+100*i)
    store_reg([val],780+100*i)
    # Bulk Voltage
    val = write_VE(i,msg_get_AbsV)
    print(573,"param Abs V",val)
    store_reg([val],774+100*i)
    return(I_max_set)


f = Find_VED()
print(579,f)
#c = 0
for c, port in enumerate(f):
    #print(373,c,port)
    if port !="null":
        com[c] = serial.Serial( port, baudrate=19200,parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS)
        #c+=1
#print(378,len(com), com,c)
time.sleep(1)
msg = msg_get_pid  #str.encode(":451"+chr(0x0a)) # get PID
I_set_max = 0

for a in range(0,4):
    #print(572,a,f[a])
    if f[a]!= "null":
        print(574,a,f[a])
        g = "()"
        x = 0
        while g == "()" or g == "-2" and x <20:
            g= write_VE(a,msg)
            time.sleep(0.2)
            x+=1
        try:
            print(545,a,"{:04x}".format(g))
        except:
            print(547,a,g)
        if (g  == 0xa046) or  (g == 0xa073):
            dev_list[a]=0
            max_list[a] = getImax(a)
            I_set_max += max_list[a]
            #Set_MPPT(a)
    
        elif g == 0xa389:
            dev_list[a]=1
            print(557,a,"shunt")
        else :
            dev_list[a]=2
print(486,dev_list,I_set_max)

#I_set_max = [70]*c
time.sleep(1.2) #wait for other program to setup and run

client = ModbusClient('localhost', port=5002)
client.connect()



#I_set_max[mppt] = get_params(mppt)
store_reg([I_set_max],792)
I_set = [800]*c
I_get = [800]*c
I_avg = [700]*5
v = True
print(578,"end of init")
a = 0
while True:
    print(580,a,dev_list)
    if dev_list[a] == 1:
        read_hex_s(a)
    elif dev_list[a]== 0:
        read_hex(a)
        f = int(read_float(11) *10)
        v_bat  = int(read_float(3)*100)
        store_reg([v_bat],788)
        #print(459,f,I_set_max[mppt])
        # if f > 700:
        #    f=700
        I_set[a] = f
        I_avg[a] = int((5*I_avg[a]+I_set[a])/6)
        if I_set[a] < I_avg[a]:
            I_avg[a] =I_set[a]
        i_tmp = int(I_avg[a]*max_list[a]/I_set_max)
        print(631,"**** I set",a,I_avg[a], i_tmp,v_bat)
        store_reg([I_avg[a]],779)
        #I_set[mppt] = 700
        ve_str = dec2hex_str(i_tmp) # adjust in proportion to unit max curreent
        val = write_VE(a,ve_str)
        print(579,a,"I set",val)

        ve_str = dec2hex_Vstr(v_bat)
        val = write_VE(a,ve_str)
        print(583,a,"V set",val)
        store_reg([val],781)
        #v = False
    a+=1
    if a > 4:
        a=0
