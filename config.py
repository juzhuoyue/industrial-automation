# PLC 通信配置
# Modbus TCP 连接参数
MODBUS_HOST = "192.168.1.100"  # PLC IP 地址
MODBUS_PORT = 502               # Modbus TCP 端口
UNIT_ID = 1                     # 从站地址

# 寄存器地址定义（ Holding Registers ）
REG_TEMPERATURE = 0            # 温度寄存器 (°C)
REG_PRESSURE = 1                # 压力寄存器 (MPa)
REG_FLOW_RATE = 2               # 流量寄存器 (m³/h)

# 报警阈值
ALARM_TEMPERATURE_MAX = 80.0    # 温度上限 (°C)
ALARM_PRESSURE_MAX = 1.0        # 压力上限 (MPa)

# 数据采集
SAMPLE_INTERVAL = 1             # 采样间隔 (秒)

# 数据库
DB_PATH = "industrial_data.db"  # SQLite 数据库路径

# Web 服务
WEB_HOST = "0.0.0.0"
WEB_PORT = 5000
