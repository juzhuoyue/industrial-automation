"""
Modbus TCP 客户端 - 负责与 PLC 通信，读取寄存器数据
"""
import logging
from typing import Optional, Dict, Tuple
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException
from config import MODBUS_HOST, MODBUS_PORT, UNIT_ID

logger = logging.getLogger(__name__)


class PLCClient:
    """Modbus TCP 客户端封装类"""

    def __init__(self):
        self.client: Optional[ModbusTcpClient] = None
        self.connected = False

    def connect(self) -> bool:
        """
        建立与 PLC 的 TCP 连接
        :return: 连接是否成功
        """
        try:
            self.client = ModbusTcpClient(
                host=MODBUS_HOST,
                port=MODBUS_PORT,
                timeout=5
            )
            # 测试连接：读取一个寄存器验证连通性
            self.client.read_holding_registers(address=0, count=1, slave=UNIT_ID)
            self.connected = True
            logger.info(f"PLC 连接成功: {MODBUS_HOST}:{MODBUS_PORT}")
            return True
        except ModbusException as e:
            logger.error(f"PLC 连接失败: {e}")
            self.connected = False
            return False

    def read_holding_registers(self, address: int, count: int = 1) -> Optional[list]:
        """
        读取保持寄存器（Hold Registers）
        :param address: 寄存器起始地址
        :param count: 读取寄存器数量
        :return: 寄存器值列表，失败返回 None
        """
        if not self.connected or self.client is None:
            logger.warning("PLC 未连接，尝试重新连接...")
            if not self.connect():
                return None
        try:
            result = self.client.read_holding_registers(
                address=address,
                count=count,
                slave=UNIT_ID
            )
            if hasattr(result, 'registers'):
                return result.registers
            logger.error(f"读取寄存器 {address} 失败: 无效响应")
            return None
        except ModbusException as e:
            logger.error(f"读取寄存器 {address} 异常: {e}")
            self.connected = False
            return None

    def read_sensors(self) -> Optional[Dict[str, float]]:
        """
        读取所有传感器数据（温度、压力、流量）
        :return: 传感器数据字典，失败返回 None
        """
        from config import REG_TEMPERATURE, REG_PRESSURE, REG_FLOW_RATE

        registers = self.read_holding_registers(address=REG_TEMPERATURE, count=3)
        if registers is None:
            return None

        # 将整数寄存器值转换为实际物理量
        # 假设寄存器值为整数，需要根据实际 PLC 配置进行比例换算
        # 这里按 10 倍比例（例如寄存器值 800 -> 80.0°C）
        return {
            "temperature": registers[0] / 10.0,  # °C
            "pressure": registers[1] / 1000.0,  # MPa
            "flow_rate": registers[2] / 100.0   # m³/h
        }

    def disconnect(self):
        """关闭 PLC 连接"""
        if self.client:
            self.client.close()
            self.connected = False
            logger.info("PLC 连接已关闭")

    def is_connected(self) -> bool:
        """检查连接状态"""
        if not self.connected or self.client is None:
            return False
        # 尝试读取一个寄存器检测连接是否存活
        try:
            self.client.read_holding_registers(address=0, count=1, slave=UNIT_ID)
            return True
        except ModbusException:
            self.connected = False
            return False
