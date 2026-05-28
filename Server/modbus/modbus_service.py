from pymodbus.client import ModbusTcpClient
import sys
import time

coil = int(sys.argv[1])

client = ModbusTcpClient("127.0.0.1", port=502)

connection = client.connect()

print("Connected:", connection)

result_on = client.write_coil(coil, True)

print("ON Result:", result_on)

time.sleep(1)

result_off = client.write_coil(coil, False)

print("OFF Result:", result_off)

client.close()

print(f"Coil {coil} Triggered")