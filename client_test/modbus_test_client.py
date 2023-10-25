import time

from pymodbus.client.sync import ModbusTcpClient

client = ModbusTcpClient(host='192.168.100.77', port=5020)
a = client.read_holding_registers(0, count=10)
print(a.registers)
try:
    a = client.write_registers(0, [1,1])
except Exception as e:
    print(e)
a = client.read_holding_registers(0, count=10)
print(a.registers)
client.close()
while True:
    time.sleep(1)
