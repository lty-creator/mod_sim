from pymodbus.server.sync import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from threading import Thread
import time


# 创建一个Modbus数据块类，并重写setValues方法


class CustomDataBlock(ModbusSequentialDataBlock):
    def setValues(self, address, values):
        # （从1开始）1,5,6,7,11,12是写寄存器，3号读寄存器反映设备状态
        self.write_related_read(address, values)
        print(f"写入值到地址 {address}：{values}")
        super().setValues(address, values)

    def write_related_read(self, address, values):
        for i in range(len(values)):
            tmp_address = address + i
            value = values[i]
            if tmp_address == 1:
                res = bin(value)[2:]
                bit_3 = res[3:4]  # 水泵启动
                bit_4 = res[4:5]  # 风机启动
                bit_7 = res[7:8]  # 水平区域指令模式
                bit_8 = res[8:9]  # 上下区域指令模式
                register_3 = int(bit_3) * (2 ** 3) + int(bit_4) * (2 ** 4) + int(bit_7) * (2 ** 10) + int(bit_8) * (
                        2 ** 11) + (
                                     2 ** 9)
                super().setValues(3, [register_3])
            elif tmp_address == 5:
                pass
            elif tmp_address == 6:
                pass
            elif tmp_address == 7:
                pass
            elif tmp_address == 11:
                pass
            elif tmp_address == 12:
                pass


# 创建一个Modbus数据块，用于存储寄存器的值
store = ModbusSlaveContext(
    di=ModbusSequentialDataBlock(0, [0] * 100),  # 离散输入寄存器
    co=ModbusSequentialDataBlock(0, [0] * 100),  # 线圈
    hr=CustomDataBlock(0, [0] * 100),  # 保持寄存器
    ir=ModbusSequentialDataBlock(0, [0] * 100))  # 输入寄存器

context = ModbusServerContext(slaves=store, single=True)

# 定义Modbus TCP服务器的IP地址和端口号
address = "192.168.100.77"
port = 5020

# 创建一个线程来运行Modbus TCP服务器
server_thread = Thread(target=StartTcpServer, args=(context,), kwargs={"address": (address, port)})
server_thread.daemon = True
server_thread.start()

# 在主线程中保持运行，以便能够监听写入值的过程
while True:
    time.sleep(1)
