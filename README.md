# 工业PLC监控系统

基于 Modbus TCP 协议的工业自动化数据采集与监控系统。

## 功能特性

- ✅ **Modbus TCP 通信** — 读取 PLC 保持寄存器（温度、压力、流量）
- ✅ **实时数据存储** — SQLite 数据库持久化存储历史数据
- ✅ **Web 监控面板** — Flask 实时页面，支持 2 秒自动刷新
- ✅ **报警逻辑** — 温度 > 80°C 或压力 > 1.0MPa 触发报警
- ✅ **历史记录查询** — Web 页面展示最近 30 分钟数据

## 目录结构

```
industrial-automation/
├── config.py          # 配置文件（PLC IP、寄存器地址、阈值等）
├── plc_client.py      # Modbus TCP 客户端封装
├── database.py        # SQLite 数据库操作
├── alarm.py           # 报警逻辑管理器
├── web_server.py      # Flask Web 监控页面
├── main.py            # 主程序入口
├── requirements.txt   # Python 依赖
└── README.md          # 本文件
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 修改配置

编辑 `config.py`，根据实际 PLC 配置修改：

```python
MODBUS_HOST = "192.168.1.100"   # PLC IP 地址
MODBUS_PORT = 502               # Modbus TCP 端口
REG_TEMPERATURE = 0             # 温度寄存器地址
REG_PRESSURE = 1                # 压力寄存器地址
REG_FLOW_RATE = 2               # 流量寄存器地址
```

### 3. 运行

```bash
python main.py
```

### 4. 打开监控页面

浏览器访问：**http://localhost:5000**

## 报警阈值

| 参数 | 阈值 | 说明 |
|------|------|------|
| 温度 | > 80°C | 触发高温报警 |
| 压力 | > 1.0 MPa | 触发高压报警 |

报警触发后，同一类型报警有 60 秒冷却时间，防止频繁触发。

## API 接口

| 接口 | 说明 |
|------|------|
| `GET /` | Web 监控页面 |
| `GET /api/latest` | 最新传感器数据（JSON） |
| `GET /api/history?minutes=30` | 最近 30 分钟历史数据 |

## 模拟数据测试

在没有真实 PLC 的环境下，可以修改 `plc_client.py` 的 `read_sensors()` 方法，
返回模拟数据进行测试：

```python
import random
def read_sensors(self):
    return {
        "temperature": 50 + random.uniform(-10, 30),   # 40~80°C
        "pressure": 0.5 + random.uniform(-0.3, 0.6),    # 0.2~1.1 MPa
        "flow_rate": 10 + random.uniform(-2, 2)          # 8~12 m³/h
    }
```
