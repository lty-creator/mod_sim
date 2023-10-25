"""
2023-10-24 wp modbus 模拟服务端
支持模拟单个雾炮的信息上传和指令接收
待扩展功能：实时显示modbus服务端每个寄存器的值
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
        1号写寄存器	bit0	bit0=1表示雾炮左转命令驱动；bit0=0表示雾炮左转命令停止
                    bit1	bit1=1表示雾炮右转命令；bit1=0表示雾炮右转命令停止
                    bit2	备用
                    bit3	bit3=1水泵启动；
                    bit4	bit4=1风机启动；
                    bit5	bit5=1 上移启动；
                    bit6	bit6=1下移启动
                    bit7	bit7=1 则表示雾炮处于水平角度指令模式，bit7=0 则表示雾炮处于水平区域指令模式
                    bit8	bit8=1 则表示雾炮处于上下角度指令模式，bit8=0 则表示雾炮处于上下区域指令模式
        2号读寄存器	水平角度或区域反馈信号	"1.当雾炮处于水平角度指令模式时：获取雾炮当前水平角度（大于等于360，无效）
                                        角度定义：从雾炮左限位开始为0度，按照顺时针方向旋转的角度
                                        2.当雾炮处于水平区域指令模式时：获取雾炮当前实际区域（1，2，3有效，其他无效）。
                                        区域定义：
                                        1.区域大小：雾炮的最大工作角度/3
                                        2.区域位置：从雾炮左限位开始按照顺时针方向分布定义为1,2,3"

        3号读寄存器	bit0	bit0=1表示雾炮左转反馈
                    bit1	bit1=1表示雾炮右转反馈
                    bit2	备用
                    bit3	bit3=1表示水泵运行反馈；
                    bit4	bit4=1表示风机运行反馈；
                    bit5	bit5=1雾炮上移运行反馈；
                    bit6	bit6=1雾炮下移运行反馈；
                    bit7	bit7=1则表示到达左限位；
                    bit8	bit8=1则表示到达右限位；
                    bit9	bit9=1则表示系统在自动状态
                    bit10	bit10=1 则表示雾炮处于水平角度指令模式，bit10=0 则表示雾炮处于水平区域指令模式
                    bit11	bit11=1则表示故障报警
                    bit12	bit12=1 则表示雾炮处于上下角度指令模式，bit12=0 则表示雾炮处于上下区域指令模式
                    bit13	bit13=1 则表示到达下限位
                    bit14	bit14=1 则表示到达上限位
                    bit15	bit15=1则表示天气锁定，bit15=0则表示锁定解除状态
        4号读寄存器	上下角度或区域反馈信号	"1.当雾炮处于上下角度指令模式时：获取雾炮当前上下方向上的角度（大于等于360，无效）
                                        角度定义：从雾炮下限位开始为0度，上限制位为最大值

                                        2.当雾炮处于上下区域指令模式时：获取雾炮当前所在的实际上下区域位置（0，1，2，其他无效）
                                        区域定义：0：水平  1：向上  2：向下      其他的无效"
        5号写寄存器	雾炮水平角度或区域设定寄存器	"1.当雾炮处于水平角度指令模式时：设定雾炮水平角度指令（大于等于360，无效），是否摆动按照水平摆动控制寄存器定义执行，设定角度大于雾炮最大水平角度，按照雾炮水平最大角度处理
                                            角度定义：从雾炮左限位开始为0度，按照顺时针方向旋转的角度
                                            2.当雾炮处于水平区域指令模式时：设定雾炮区域指令（1，2，3，4有效，其他无效），雾炮停止到雾炮区域中心（是否摆动按照水平摆动控制寄存器定义执行）。
                                            区域定义：
                                            1.区域大小：雾炮的最大工作角度/3
                                            2.区域位置：从雾炮左限位开始按照顺时针方向分布定义为1,2,3
                                                                4表示全区域"
        6号写寄存器	word	心跳（最大间隔60秒）
        7号写寄存器	雾炮水平摆动控制寄存器	"1.当雾炮处于水平角度指令模式时：设定雾炮水平摆动幅度。定义如下：以雾炮水平角度控制寄存器位中心角，以设定摆动角度在中心角左右摆动。其中： 有效值：0～180，0:不摆动；其他值：不摆动
                                         2.当雾炮处于水平区域指令模式时：设定雾炮是否在区域内摆动指令定义如下：1: 摆动 其他:不摆动"


        :param address:
        :param values:
        :return: none
        """
        # （从1开始）1,5,6,7,11,12是写寄存器，3号读寄存器反映设备状态
        self.write_related_read(address, values)
        print(f"写入值到地址 {address}：{values}")
        super().setValues(address, values)

    def write_related_read(self, address, values):
        for i in range(len(values)):
            tmp_address = address + i
            value = values[i]
            if tmp_address == 1:
                res = '0' * 16 + bin(value)[2:]
                bit_3 = res[-4:-3]  # 水泵启动
                bit_4 = res[-5:-4]  # 风机启动
                bit_7 = res[-8:-7]  # 水平区域指令模式
                bit_8 = res[-9:-8]  # 上下区域指令模式
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


class ModSimWp:
    def __init__(self, address: str, port: int):
        mod_sim_wp_thread = Thread(target=self.mod_sim_wp, kwargs={"address": address, 'port': port})
        mod_sim_wp_thread.start()

    def mod_sim_wp(self, address, port):
        # 创建一个Modbus数据块，用于存储寄存器的值
        store = ModbusSlaveContext(
            di=ModbusSequentialDataBlock(0, [0] * 100),  # 离散输入寄存器
            co=ModbusSequentialDataBlock(0, [0] * 100),  # 线圈
            hr=CustomDataBlock(0, [0] * 100),  # 保持寄存器
            ir=ModbusSequentialDataBlock(0, [0] * 100))  # 输入寄存器

        context = ModbusServerContext(slaves=store, single=True)

        # 创建一个线程来运行Modbus TCP服务器
        server_thread = Thread(target=StartTcpServer, args=(context,), kwargs={"address": (address, port)})
        server_thread.daemon = True
        server_thread.start()

        # 在主线程中保持运行，以便能够监听写入值的过程
        while True:
            time.sleep(1)
