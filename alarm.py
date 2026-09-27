"""
报警逻辑模块 - 检测异常并触发报警
"""
import logging
from typing import Dict, Tuple, Optional
from datetime import datetime
from config import ALARM_TEMPERATURE_MAX, ALARM_PRESSURE_MAX
from database import insert_alarm_log

logger = logging.getLogger(__name__)


class AlarmManager:
    """报警管理器"""

    def __init__(self):
        # 上一次报警时间（避免同一报警短时间内重复触发）
        self._last_alarm_time: Dict[str, float] = {}
        # 报警冷却时间（秒）
        self._alarm_cooldown = 60
        # 当前报警状态
        self._active_alarms: Dict[str, bool] = {
            "temperature": False,
            "pressure": False
        }

    def check_and_alarm(self, temperature: float, pressure: float) -> Tuple[bool, Optional[str]]:
        """
        检查传感器数据是否触发报警条件
        :param temperature: 当前温度 (°C)
        :param pressure: 当前压力 (MPa)
        :return: (是否触发报警, 报警消息或 None)
        """
        alarms_triggered = []
        now = datetime.now().timestamp()

        # 检查温度报警
        if temperature > ALARM_TEMPERATURE_MAX:
            alarm_key = "temperature"
            if self._can_trigger_alarm(alarm_key, now):
                msg = f"温度报警！当前: {temperature:.1f}°C, 阈值: {ALARM_TEMPERATURE_MAX}°C"
                alarms_triggered.append(msg)
                insert_alarm_log("temperature", temperature,
                                 ALARM_TEMPERATURE_MAX, msg)
                self._last_alarm_time[alarm_key] = now
                self._active_alarms[alarm_key] = True
                logger.warning(msg)

        # 检查压力报警
        if pressure > ALARM_PRESSURE_MAX:
            alarm_key = "pressure"
            if self._can_trigger_alarm(alarm_key, now):
                msg = f"压力报警！当前: {pressure:.3f}MPa, 阈值: {ALARM_PRESSURE_MAX}MPa"
                alarms_triggered.append(msg)
                insert_alarm_log("pressure", pressure,
                                 ALARM_PRESSURE_MAX, msg)
                self._last_alarm_time[alarm_key] = now
                self._active_alarms[alarm_key] = True
                logger.warning(msg)

        if alarms_triggered:
            return True, " | ".join(alarms_triggered)
        return False, None

    def _can_trigger_alarm(self, alarm_key: str, current_time: float) -> bool:
        """
        检查是否可以触发报警（考虑冷却时间）
        """
        if alarm_key not in self._last_alarm_time:
            return True
        elapsed = current_time - self._last_alarm_time[alarm_key]
        return elapsed >= self._alarm_cooldown

    def get_active_alarms(self) -> Dict[str, bool]:
        """获取当前活跃报警状态"""
        return self._active_alarms.copy()

    def clear_alarm(self, alarm_type: str):
        """手动清除某个报警状态"""
        if alarm_type in self._active_alarms:
            self._active_alarms[alarm_type] = False
            logger.info(f"报警已手动清除: {alarm_type}")

    def reset_all(self):
        """重置所有报警状态"""
        self._active_alarms = {k: False for k in self._active_alarms}
        self._last_alarm_time.clear()
