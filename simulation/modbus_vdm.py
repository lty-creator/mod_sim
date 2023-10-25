"""

2023-10-24,vdm modbus 模拟服务端
"""

from pymodbus.server.sync import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from threading import Thread
import time


# 创建一个Modbus数据块类，并重写setValues方法


class CustomDataBlock(ModbusSequentialDataBlock):
    def setValues(self, address, values):
        """
        （从0开始）
        0	云台水平角度	 	只读
        1	云台仰角	 	只读
        2	VDM数值	 	只读
        3	报警状态		只读
        4	车辆目标数量	 	只读
        5	烟羽识别目标数量	 	只读
        6	云台旋转的开始角度	按照顺时针旋转 	只读
        7	云台旋转的结束角度		只读
        8	保留		只读
        9	云台水平角度设定		只写
        10	云台仰角设定		只写
        """

        self.write_related_read(address, values)
        print(f"写入值到地址 {address}：{values}")
        super().setValues(address, values)

    def write_related_read(self, address, values):
        # 这个函数运行失败不会报错
        for i in range(len(values)):
            tmp_address = address + i
            value = values[i]
            if tmp_address == 10:
                super().setValues(1, [value])
            elif tmp_address == 11:
                super().setValues(2, [value])


class ModSimVdm:
    def __int__(self, address, port):
        mod_sim_vdm_thread = Thread(target=self.mod_sim_vdm, kwargs={"address": address, 'port': port})
        mod_sim_vdm_thread.start()

    # 创建一个Modbus数据块，用于存储寄存器的值
    def mod_sim_vdm(self, address, port):
        store = ModbusSlaveContext(
            di=ModbusSequentialDataBlock(0, [0] * 100),  # 离散输入寄存器
            co=ModbusSequentialDataBlock(0, [0] * 100),  # 线圈
            hr=CustomDataBlock(0, [0] * 160),  # 保持寄存器
            ir=ModbusSequentialDataBlock(0, [0] * 100))  # 输入寄存器

        context = ModbusServerContext(slaves=store, single=True)

        # 定义Modbus TCP服务器的IP地址和端口号

        # 创建一个线程来运行Modbus TCP服务器
        server_thread = Thread(target=StartTcpServer, args=(context,), kwargs={"address": (address, port)})
        server_thread.daemon = True
        server_thread.start()

        # 在主线程中保持运行，以便能够监听写入值的过程
        while True:
            time.sleep(1)
