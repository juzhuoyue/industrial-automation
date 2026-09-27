"""
主程序入口 - 启动数据采集循环
"""
import sys
import time
import signal
import logging
from threading import Thread

from config import SAMPLE_INTERVAL
from plc_client import PLCClient
from database import init_db, insert_sensor_data, get_latest_data
from alarm import AlarmManager

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("monitor.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

# 全局停止标志
running = True


def signal_handler(signum, frame):
    """捕获 Ctrl+C 信号，优雅退出"""
    global running
    logger.info("收到退出信号，正在关闭...")
    running = False


def data_collection_loop(plc: PLCClient, alarm_mgr: AlarmManager):
    """
    数据采集主循环
    :param plc: PLC 客户端实例
    :param alarm_mgr: 报警管理器实例
    """
    logger.info("数据采集循环启动")
    consecutive_failures = 0
    max_consecutive_failures = 5

    while running:
        try:
            # 读取传感器数据
            sensors = plc.read_sensors()
            if sensors is None:
                consecutive_failures += 1
                logger.warning(f"读取PLC数据失败 ({consecutive_failures}/{max_consecutive_failures})")
                if consecutive_failures >= max_consecutive_failures:
                    logger.error("连续失败次数过多，尝试重新连接PLC...")
                    plc.connect()
                    consecutive_failures = 0
                time.sleep(SAMPLE_INTERVAL)
                continue

            consecutive_failures = 0
            temperature = sensors["temperature"]
            pressure = sensors["pressure"]
            flow_rate = sensors["flow_rate"]

            # 检查报警条件
            alarm_triggered, alarm_msg = alarm_mgr.check_and_alarm(
                temperature, pressure
            )

            # 存入数据库
            success = insert_sensor_data(
                temperature=temperature,
                pressure=pressure,
                flow_rate=flow_rate,
                alarm_triggered=alarm_triggered
            )

            if alarm_triggered:
                logger.warning(f"⚠️ 报警: {alarm_msg}")

            status = "⚠️ 报警" if alarm_triggered else "✓ 正常"
            logger.info(
                f"数据: 温度={temperature:.1f}°C | "
                f"压力={pressure:.3f}MPa | "
                f"流量={flow_rate:.2f}m³/h | "
                f"{status}"
            )

        except Exception as e:
            logger.error(f"采集循环异常: {e}")
            consecutive_failures += 1

        time.sleep(SAMPLE_INTERVAL)

    logger.info("数据采集循环已退出")


def main():
    global running

    logger.info("=" * 50)
    logger.info("工业PLC监控系统启动")
    logger.info("=" * 50)

    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 初始化数据库
    try:
        init_db()
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        sys.exit(1)

    # 连接 PLC
    plc = PLCClient()
    if not plc.connect():
        logger.error("PLC 连接失败，程序退出")
        sys.exit(1)

    # 初始化报警管理器
    alarm_mgr = AlarmManager()

    # 启动 Web 服务线程
    from web_server import run_web_server
    from config import WEB_HOST, WEB_PORT
    web_thread = Thread(target=run_web_server, args=(WEB_HOST, WEB_PORT), daemon=True)
    web_thread.start()
    logger.info(f"Web 监控页面: http://localhost:{WEB_PORT}")

    # 启动数据采集循环
    try:
        data_collection_loop(plc, alarm_mgr)
    finally:
        plc.disconnect()
        logger.info("监控系统已关闭")


if __name__ == "__main__":
    main()
