"""
Flask Web 监控服务器 - 提供实时数据展示和报警状态页面
"""
import logging
from flask import Flask, render_template_string, jsonify
from database import get_latest_data, get_recent_data
from alarm import AlarmManager

logger = logging.getLogger(__name__)
app = Flask(__name__)

# 共享报警管理器实例
alarm_mgr = AlarmManager()


# HTML 模板（内嵌，无需额外文件）
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>工业监控系统</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #1a1a2e; color: #eee; min-height: 100vh; }
        .header { background: #16213e; padding: 20px 40px; border-bottom: 2px solid #0f3460; }
        .header h1 { color: #00d9ff; font-size: 24px; }
        .header .subtitle { color: #888; font-size: 13px; margin-top: 4px; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px 40px; }
        .status-bar { display: flex; gap: 15px; margin-bottom: 25px; align-items: center; }
        .status-indicator { display: flex; align-items: center; gap: 8px; font-size: 13px; }
        .dot { width: 10px; height: 10px; border-radius: 50%; }
        .dot.green { background: #00ff88; box-shadow: 0 0 8px #00ff88; }
        .dot.red { background: #ff4444; box-shadow: 0 0 8px #ff4444; animation: blink 1s infinite; }
        @keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }
        .sensors { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 25px; }
        .card { background: #16213e; border-radius: 12px; padding: 22px; border: 1px solid #0f3460; }
        .card.alert { border-color: #ff4444; background: #1e0a0a; }
        .card h3 { color: #888; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }
        .card .value { font-size: 36px; font-weight: bold; margin-bottom: 5px; }
        .card .unit { font-size: 14px; color: #888; }
        .card.temp .value { color: #ff6b35; }
        .card.pressure .value { color: #00d9ff; }
        .card.flow .value { color: #00ff88; }
        .card.alert .value { color: #ff4444 !important; }
        .alarm-banner { display: none; background: linear-gradient(90deg, #ff4444, #cc0000); color: white; padding: 12px 20px; border-radius: 8px; margin-bottom: 20px; font-weight: bold; text-align: center; animation: alarm-pulse 2s infinite; }
        .alarm-banner.show { display: block; }
        @keyframes alarm-pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.7; } }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th { background: #0f3460; padding: 10px 12px; text-align: left; font-size: 12px; color: #00d9ff; }
        td { padding: 8px 12px; border-bottom: 1px solid #0f3460; font-size: 13px; }
        tr:hover { background: #16213e; }
        .footer { text-align: center; padding: 20px; color: #555; font-size: 12px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏭 工业PLC监控系统</h1>
        <div class="subtitle">Modbus TCP · SQLite · Flask</div>
    </div>
    <div class="container">
        <div id="alarmBanner" class="alarm-banner">⚠️ 报警触发！请立即检查系统！</div>
        <div class="status-bar">
            <div class="status-indicator"><span id="plcStatus" class="dot red"></span> PLC连接</div>
            <div class="status-indicator"><span id="dbStatus" class="dot green"></span> 数据库</div>
            <div class="status-indicator">最后更新: <span id="lastUpdate">--</span></div>
        </div>
        <div class="sensors">
            <div id="tempCard" class="card temp">
                <h3>🌡️ 温度</h3>
                <div class="value" id="tempValue">--</div>
                <div class="unit">°C &nbsp;|&nbsp; 阈值: {{ config.ALARM_TEMPERATURE_MAX }}°C</div>
            </div>
            <div id="pressCard" class="card pressure">
                <h3>📊 压力</h3>
                <div class="value" id="pressValue">--</div>
                <div class="unit">MPa &nbsp;|&nbsp; 阈值: {{ config.ALARM_PRESSURE_MAX }}MPa</div>
            </div>
            <div class="card flow">
                <h3>💧 流量</h3>
                <div class="value" id="flowValue">--</div>
                <div class="unit">m³/h</div>
            </div>
        </div>
        <h2 style="color:#00d9ff; margin-bottom:12px; font-size:16px;">📋 最近记录</h2>
        <div style="overflow-x:auto;">
            <table>
                <thead><tr>
                    <th>时间</th><th>温度 (°C)</th><th>压力 (MPa)</th><th>流量 (m³/h)</th><th>状态</th>
                </tr></thead>
                <tbody id="dataTable"><tr><td colspan="5">加载中...</td></tr></tbody>
            </table>
        </div>
        <div class="footer">Industrial Automation Monitor · {{ config.MODBUS_HOST }}:{{ config.MODBUS_PORT }}</div>
    </div>
    <script>
        let alarmActive = false;
        async function fetchData() {
            try {
                const [latest, history] = await Promise.all([
                    fetch('/api/latest').then(r => r.json()),
                    fetch('/api/history?minutes=30').then(r => r.json())
                ]);
                if (latest) {
                    document.getElementById('plcStatus').className = 'dot green';
                    document.getElementById('lastUpdate').textContent = latest.timestamp || '--';
                    document.getElementById('tempValue').textContent = latest.temperature?.toFixed(1) || '--';
                    document.getElementById('pressValue').textContent = latest.pressure?.toFixed(3) || '--';
                    document.getElementById('flowValue').textContent = latest.flow_rate?.toFixed(2) || '--';
                    const isAlarm = latest.alarm_triggered;
                    if (isAlarm) {
                        document.getElementById('alarmBanner').className = 'alarm-banner show';
                        document.getElementById('tempCard').className = 'card temp alert';
                        document.getElementById('pressCard').className = 'card pressure alert';
                    } else {
                        document.getElementById('alarmBanner').className = 'alarm-banner';
                        document.getElementById('tempCard').className = 'card temp';
                        document.getElementById('pressCard').className = 'card pressure';
                    }
                }
                if (history && history.length) {
                    const rows = history.map(r => `<tr>
                        <td>${r.timestamp}</td>
                        <td style="color:${r.temperature > ${50} ? '#ff6b35' : '#eee'}">${r.temperature?.toFixed(1)}</td>
                        <td style="color:${r.pressure > ${0.7} ? '#00d9ff' : '#eee'}">${r.pressure?.toFixed(3)}</td>
                        <td>${r.flow_rate?.toFixed(2)}</td>
                        <td>${r.alarm_triggered ? '<span style="color:#ff4444">⚠ 报警</span>' : '<span style="color:#00ff88">✓ 正常</span>'}</td>
                    </tr>`).join('');
                    document.getElementById('dataTable').innerHTML = rows || '<tr><td colspan="5">暂无数据</td></tr>';
                }
            } catch (e) {
                document.getElementById('plcStatus').className = 'dot red';
                console.error('数据获取失败:', e);
            }
        }
        setInterval(fetchData, 2000);
        fetchData();
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    """主页 - 监控仪表板"""
    from config import ALARM_TEMPERATURE_MAX, ALARM_PRESSURE_MAX, MODBUS_HOST, MODBUS_PORT
    return render_template_string(
        HTML_TEMPLATE,
        config=type('Config', (), {
            'ALARM_TEMPERATURE_MAX': ALARM_TEMPERATURE_MAX,
            'ALARM_PRESSURE_MAX': ALARM_PRESSURE_MAX,
            'MODBUS_HOST': MODBUS_HOST,
            'MODBUS_PORT': MODBUS_PORT
        })()
    )


@app.route("/api/latest")
def api_latest():
    """获取最新传感器数据（JSON）"""
    data = get_latest_data()
    if data:
        return jsonify(data)
    return jsonify({"error": "No data"}), 404


@app.route("/api/history")
def api_history():
    """获取历史数据（JSON）"""
    from flask import request
    minutes = request.args.get("minutes", 60, type=int)
    limit = request.args.get("limit", 100, type=int)
    data = get_recent_data(minutes=minutes, limit=limit)
    return jsonify(data)


def run_web_server(host: str = "0.0.0.0", port: int = 5000):
    """启动 Web 服务器"""
    logger.info(f"Web 服务启动: http://{host}:{port}")
    app.run(host=host, port=port, debug=False, threaded=True)
