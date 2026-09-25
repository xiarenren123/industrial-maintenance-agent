import json
import uuid
from datetime import datetime
from pathlib import Path


RECORDS_PATH = Path(__file__).parent / "data" / "maintenance_records.json"


def load_maintenance_records() -> list[dict]:
    """读取全部维护记录；文件不存在、为空或格式错误时返回空列表。"""
    if not RECORDS_PATH.exists():
        return []
    try:
        content = RECORDS_PATH.read_text(encoding="utf-8").strip()
        if not content:
            return []
        records = json.loads(content)
        return records if isinstance(records, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def save_maintenance_record(
    equipment_type: str,
    fault_description: str,
    analysis_result: str,
    status: str = "待处理",
) -> dict:
    """保存一条维护记录，并返回刚保存的记录。"""
    record = {
        "id": str(uuid.uuid4()),
        "created_at": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S"),
        "equipment_type": equipment_type,
        "fault_description": fault_description,
        "analysis_result": analysis_result,
        "status": status,
    }
    records = load_maintenance_records()
    records.append(record)
    RECORDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECORDS_PATH.write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return record
