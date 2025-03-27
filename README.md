# VE-direct-1
Repository changed to include Mk3/USB for Inverter direct control
VE7_0 : Ve direct hex code
Reads multiple MPPT &amp; Shunt over VE-direct , loads data to modbus server
NOTE:
This program also SETS the NV RAM in the MPPT for the lithium battery voltage parameters every time it starts.
Frequent re-starting of this code may wear out the NV RAM.
To do: check the set parameters BEFORE stting them, only set if changed.


Mk3_inv_2.py: This interfaces to a VE-Bus inverter using a Mk2 or Mk3 interface. This code has been recently extended to include the direct controll of the ESS assistant. One should carefully check tha RAm Var download to ensure that the Ram Var Write (0x83) is on the right assistant. Also check to see if your inverters grid code permits export form DC, the As4777.2020 codes do not!!
