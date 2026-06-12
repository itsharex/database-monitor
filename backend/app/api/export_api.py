"""
数据导出与报表 API。
"""

import csv
import io
import json
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.api.deps import require_auth
from app.models.user import User
from app.schemas.metrics import ExportRequest
from app.services.dashboard_service import dashboard_service
from app.services.influxdb_service import influxdb_service

router = APIRouter(prefix="/export", tags=["数据导出"])


@router.post("/data")
async def export_data(data: ExportRequest, _user: User = Depends(require_auth)):
    """导出监控数据为 CSV 或 JSON。"""
    metric_names = data.metric_names or ["qps", "connections", "cpu_usage"]
    start_str = data.start_time.isoformat()
    stop_str = data.end_time.isoformat()

    if data.instance_id:
        series_list = influxdb_service.query_metrics(
            data.instance_id, metric_names, start=start_str, stop=stop_str
        )
    else:
        series_list = []

    if data.format == "json":
        export_data = [
            {
                "metric_name": s.metric_name,
                "points": [{"timestamp": p.timestamp.isoformat(), "value": p.value} for p in s.points],
            }
            for s in series_list
        ]
        content = json.dumps(export_data, ensure_ascii=False, indent=2)
        return StreamingResponse(
            io.BytesIO(content.encode()),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=metrics_export.json"},
        )

    # CSV 格式
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["metric_name", "timestamp", "value"])
    for series in series_list:
        for point in series.points:
            writer.writerow([series.metric_name, point.timestamp.isoformat(), point.value])

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=metrics_export.csv"},
    )


@router.get("/report/pdf")
async def export_pdf_report(_user: User = Depends(require_auth)):
    """生成 PDF 监控报告。"""
    kpi = await dashboard_service.get_kpi()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("数据库监控报告", styles["Title"]))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))
    elements.append(Spacer(1, 20))

    table_data = [
        ["指标", "数值"],
        ["监控实例总数", str(kpi.total_instances)],
        ["异常实例数", str(kpi.abnormal_instances)],
        ["平均 QPS", f"{kpi.avg_qps:.2f}"],
        ["总连接数", f"{kpi.total_connections:.0f}"],
        ["今日告警数", str(kpi.today_alerts)],
        ["系统健康度", f"{kpi.health_score:.1f}%"],
    ]
    table = Table(table_data, colWidths=[200, 200])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a2332")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 12),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=monitor_report.pdf"},
    )
