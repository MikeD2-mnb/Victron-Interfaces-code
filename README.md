# VE-direct-1
Reads multiple MPPT &amp; Shunt over VE-direct , loads data to modbus server
NOTE:
This program also SETS the NV RAM in the MPPT for the lithium battery voltage parameters every time it starts.
Frequent re-starting of this code may wear out the NV RAM.
To do: check the set parameters BEFORE stting them, only set if changed.
