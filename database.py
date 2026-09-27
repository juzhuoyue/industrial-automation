"""
SQLite 数据库操作 - 存储传感器历史数据
"""
import sqlite3
import logging
from datetime import datetime
from typing import Optional, List, Dict
from config import DB_PATH

logger = logging.getLogger(__name__)


def init_db():
    """
    初始化数据库，创建数据表（如果不存在）
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sensor_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    temperature REAL,
                    pressure REAL,
                    flow_rate REAL,
                    alarm_triggered INTEGER DEFAULT 0
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alarm_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    alarm_type TEXT NOT NULL,
                    alarm_value REAL,
                    threshold REAL,
                    message TEXT
                )
            """)
            # 创建索引加速查询
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sensor_timestamp
                ON sensor_data(timestamp)
            """)
            conn.commit()
            logger.info("数据库初始化完成")
    except sqlite3.Error as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


def insert_sensor_data(temperature: float, pressure: float,
                       flow_rate: float, alarm_triggered: bool = False) -> bool:
    """
    插入一条传感器数据记录
    :param temperature: 温度 (°C)
    :param pressure: 压力 (MPa)
    :param flow_rate: 流量 (m³/h)
    :param alarm_triggered: 是否触发过报警
    :return: 是否插入成功
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sensor_data
                (timestamp, temperature, pressure, flow_rate, alarm_triggered)
                VALUES (?, ?, ?, ?, ?)
            """, (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                temperature, pressure, flow_rate,
                1 if alarm_triggered else 0
            ))
            conn.commit()
            return True
    except sqlite3.Error as e:
        logger.error(f"插入传感器数据失败: {e}")
        return False


def insert_alarm_log(alarm_type: str, alarm_value: float,
                     threshold: float, message: str) -> bool:
    """
    记录一条报警日志
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO alarm_log
                (timestamp, alarm_type, alarm_value, threshold, message)
                VALUES (?, ?, ?, ?, ?)
            """, (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                alarm_type, alarm_value, threshold, message
            ))
            conn.commit()
            return True
    except sqlite3.Error as e:
        logger.error(f"插入报警日志失败: {e}")
        return False


def get_recent_data(minutes: int = 60, limit: int = 1000) -> List[Dict]:
    """
    获取最近 N 分钟的传感器数据
    :param minutes: 最近多少分钟
    :param limit: 最大返回条数
    :return: 数据记录列表
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT timestamp, temperature, pressure, flow_rate, alarm_triggered
                FROM sensor_data
                WHERE timestamp >= datetime('now', '-' || ? || ' minutes')
                ORDER BY timestamp DESC
                LIMIT ?
            """, (minutes, limit))
            rows = cursor.fetchall()
            return [
                {
                    "timestamp": row[0],
                    "temperature": row[1],
                    "pressure": row[2],
                    "flow_rate": row[3],
                    "alarm_triggered": bool(row[4])
                }
                for row in rows
            ]
    except sqlite3.Error as e:
        logger.error(f"查询传感器数据失败: {e}")
        return []


def get_latest_data() -> Optional[Dict]:
    """获取最新一条传感器数据"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT timestamp, temperature, pressure, flow_rate, alarm_triggered
                FROM sensor_data
                ORDER BY id DESC LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                return {
                    "timestamp": row[0],
                    "temperature": row[1],
                    "pressure": row[2],
                    "flow_rate": row[3],
                    "alarm_triggered": bool(row[4])
                }
            return None
    except sqlite3.Error as e:
        logger.error(f"查询最新数据失败: {e}")
        return None
