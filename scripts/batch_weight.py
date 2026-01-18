#!/usr/bin/env python3
"""批次體重記錄腳本。

功能：
1. 從 CSV 檔案批次匯入體重記錄（如果當日已有就更新，沒有就新增）
2. 批次查詢指定區間的體重記錄

用法：
  # 批次匯入
  python scripts/batch_weight.py import \
    --baby-id BABY_ID \
    --email user@example.com \
    --password "password" \
    --csv-path weights.csv

  # 批次查詢
  python scripts/batch_weight.py query \
    --baby-id BABY_ID \
    --email user@example.com \
    --password "password" \
    --from-date 2024-01-01 \
    --to-date 2024-01-31

CSV 格式（匯入）：
  日期,體重,筆記
  2024-01-15,3.5,早晨測量
  2024-01-16,3.6,晚上測量

  注意：
  - 日期格式：YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS
  - 體重單位：公斤（會自動轉換為克）
  - 筆記：可選欄位
"""

import argparse
import csv
import json
import sys
from datetime import date, datetime, time
from pathlib import Path
from typing import Any

try:
    import httpx
except ImportError:
    print("❌ 缺少 httpx 套件，請先安裝：")
    print("   pip install httpx")
    print("   或")
    print("   uv pip install httpx")
    sys.exit(1)


# API 設定
KONG_URL = "https://kong-gateway-dev-ggofz32qfa-de.a.run.app"


def login(email: str, password: str) -> str:
    """登入並取得 JWT token."""
    url = f"{KONG_URL}/auth/token"
    with httpx.Client(timeout=30.0) as http_client:
        response = http_client.post(
            url,
            json={"email": email, "password": password},
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        data = response.json()
        token = data.get("access_token")
        if not token:
            raise ValueError("Failed to get access_token from login response")
        return token


def get_headers(token: str) -> dict[str, str]:
    """取得 API 請求 headers."""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def list_weights(
    baby_id: str, token: str, from_date: datetime | None = None, to_date: datetime | None = None
) -> list[dict[str, Any]]:
    """查詢體重記錄列表."""
    url = f"{KONG_URL}/v1/babies/{baby_id}/weights"
    params: dict[str, Any] = {}
    if from_date:
        params["from"] = from_date.isoformat()
    if to_date:
        params["to"] = to_date.isoformat()

    with httpx.Client(timeout=30.0) as http_client:
        response = http_client.get(url, headers=get_headers(token), params=params)
        response.raise_for_status()
        return response.json()


def create_weight(
    baby_id: str, token: str, timestamp: datetime, weight_g: int, note: str | None = None
) -> dict[str, Any]:
    """新增體重記錄."""
    url = f"{KONG_URL}/v1/babies/{baby_id}/weights"
    data: dict[str, Any] = {
        "timestamp": timestamp.isoformat(),
        "weight_g": weight_g,
    }
    if note:
        data["note"] = note

    with httpx.Client(timeout=30.0) as http_client:
        response = http_client.post(url, headers=get_headers(token), json=data)
        response.raise_for_status()
        return response.json()


def update_weight(
    baby_id: str,
    weight_id: str,
    token: str,
    timestamp: datetime | None = None,
    weight_g: int | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    """更新體重記錄."""
    url = f"{KONG_URL}/v1/babies/{baby_id}/weights/{weight_id}"
    data: dict[str, Any] = {}
    if timestamp:
        data["timestamp"] = timestamp.isoformat()
    if weight_g is not None:
        data["weight_g"] = weight_g
    if note is not None:
        data["note"] = note

    with httpx.Client(timeout=30.0) as http_client:
        response = http_client.put(url, headers=get_headers(token), json=data)
        response.raise_for_status()
        return response.json()


def find_weight_by_date(weights: list[dict[str, Any]], target_date: date) -> dict[str, Any] | None:
    """從體重記錄列表中找出指定日期的記錄（同一天即可）。"""
    for weight in weights:
        timestamp_str = weight.get("timestamp")
        if not timestamp_str:
            continue
        try:
            # 解析 ISO 8601 格式
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            if timestamp.date() == target_date:
                return weight
        except (ValueError, AttributeError):
            continue
    return None


def parse_date(date_str: str) -> datetime:
    """解析日期字串。

    支援格式：
    - YYYY-MM-DD
    - YYYY-MM-DD HH:MM:SS
    - YYYY-MM-DDTHH:MM:SS
    """
    # 嘗試多種格式
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    raise ValueError(f"Invalid date format: {date_str}")


def parse_weight(weight_str: str) -> int:
    """解析體重字串（公斤）並轉換為克。"""
    try:
        weight_kg = float(weight_str.strip())
        weight_g = int(weight_kg * 1000)
        if weight_g <= 0 or weight_g >= 100000:
            raise ValueError(f"Weight {weight_g}g is out of valid range (0-100000g)")
        return weight_g
    except ValueError as e:
        raise ValueError(f"Invalid weight format: {weight_str}") from e


def import_from_csv(baby_id: str, email: str, password: str, csv_path: str) -> None:
    """從 CSV 檔案批次匯入體重記錄。"""
    csv_file = Path(csv_path)
    if not csv_file.exists():
        print(f"❌ CSV 檔案不存在: {csv_path}")
        sys.exit(1)

    print(f"📂 讀取 CSV 檔案: {csv_path}")
    print(f"👶 Baby ID: {baby_id}")
    print()

    # 登入
    print("🔐 登入中...")
    try:
        token = login(email, password)
        print("✅ 登入成功")
    except Exception as e:
        print(f"❌ 登入失敗: {e}")
        sys.exit(1)

    # 讀取現有記錄（用於判斷是否已存在）
    print("📋 查詢現有體重記錄...")
    try:
        existing_weights = list_weights(baby_id, token)
        print(f"✅ 找到 {len(existing_weights)} 筆現有記錄")
    except Exception as e:
        print(f"⚠️  查詢現有記錄失敗: {e}")
        existing_weights = []

    # 讀取 CSV
    print()
    print("📖 讀取 CSV 資料...")
    records: list[dict[str, Any]] = []
    try:
        with csv_file.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):  # 從第 2 行開始（第 1 行是標題）
                try:
                    # 解析欄位（支援多種欄位名稱）
                    date_str = (
                        row.get("日期")
                        or row.get("date")
                        or row.get("Date")
                        or row.get("timestamp")
                    )
                    weight_str = (
                        row.get("體重")
                        or row.get("weight")
                        or row.get("Weight")
                        or row.get("weight_kg")
                    )
                    note_str = (
                        row.get("筆記")
                        or row.get("note")
                        or row.get("Note")
                        or row.get("備註")
                        or ""
                    )

                    if not date_str or not weight_str:
                        print(f"⚠️  第 {row_num} 行缺少必要欄位（日期或體重），已跳過")
                        continue

                    timestamp = parse_date(date_str)
                    weight_g = parse_weight(weight_str)
                    note = note_str.strip() if note_str else None

                    records.append(
                        {
                            "row": row_num,
                            "timestamp": timestamp,
                            "weight_g": weight_g,
                            "note": note,
                        }
                    )
                except ValueError as e:
                    print(f"⚠️  第 {row_num} 行資料格式錯誤: {e}，已跳過")
                    continue
    except Exception as e:
        print(f"❌ 讀取 CSV 失敗: {e}")
        sys.exit(1)

    print(f"✅ 成功讀取 {len(records)} 筆記錄")
    print()

    # 批次處理
    print("🔄 開始批次匯入...")
    success_count = 0
    update_count = 0
    create_count = 0
    error_count = 0

    for record in records:
        row_num = record["row"]
        timestamp = record["timestamp"]
        weight_g = record["weight_g"]
        note = record["note"]

        try:
            # 檢查當日是否已有記錄
            existing_weight = find_weight_by_date(existing_weights, timestamp.date())
            if existing_weight:
                # 更新現有記錄
                weight_id = existing_weight["weight_id"]
                print(
                    f"📝 第 {row_num} 行：更新 {timestamp.date()} 的記錄 (ID: {weight_id[:8]}...)"
                )
                update_weight(
                    baby_id, weight_id, token, timestamp=timestamp, weight_g=weight_g, note=note
                )
                update_count += 1
            else:
                # 新增記錄
                print(f"➕ 第 {row_num} 行：新增 {timestamp.date()} 的記錄")
                create_weight(baby_id, token, timestamp, weight_g, note)
                create_count += 1
            success_count += 1
        except Exception as e:
            print(f"❌ 第 {row_num} 行處理失敗: {e}")
            error_count += 1

    # 統計結果
    print()
    print("=" * 50)
    print("📊 匯入結果統計")
    print("=" * 50)
    print(f"✅ 成功: {success_count} 筆")
    print(f"  - 新增: {create_count} 筆")
    print(f"  - 更新: {update_count} 筆")
    print(f"❌ 失敗: {error_count} 筆")
    print("=" * 50)


def query_weights(
    baby_id: str,
    email: str,
    password: str,
    from_date: date | None = None,
    to_date: date | None = None,
    output_format: str = "table",
) -> None:
    """批次查詢體重記錄。"""
    print(f"👶 Baby ID: {baby_id}")
    if from_date:
        print(f"📅 起始日期: {from_date}")
    if to_date:
        print(f"📅 結束日期: {to_date}")
    print()

    # 登入
    print("🔐 登入中...")
    try:
        token = login(email, password)
        print("✅ 登入成功")
    except Exception as e:
        print(f"❌ 登入失敗: {e}")
        sys.exit(1)

    # 查詢記錄
    print()
    print("📋 查詢體重記錄...")
    try:
        from_datetime = datetime.combine(from_date, time.min) if from_date else None
        to_datetime = datetime.combine(to_date, time.max) if to_date else None
        weights = list_weights(baby_id, token, from_datetime, to_datetime)
        print(f"✅ 找到 {len(weights)} 筆記錄")
    except Exception as e:
        print(f"❌ 查詢失敗: {e}")
        sys.exit(1)

    # 輸出結果
    print()
    if output_format == "json":
        # JSON 格式輸出
        print(json.dumps(weights, indent=2, ensure_ascii=False, default=str))
    else:
        # 表格格式輸出
        if not weights:
            print("📭 沒有找到任何記錄")
            return

        print("=" * 100)
        print(f"{'日期':<20} {'體重（公斤）':<15} {'體重（克）':<12} {'筆記':<40} {'ID':<25}")
        print("=" * 100)
        for weight in weights:
            timestamp_str = weight.get("timestamp", "")
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                date_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, AttributeError):
                date_str = str(timestamp_str)

            weight_g = weight.get("weight_g", 0)
            weight_kg = weight_g / 1000.0
            note = weight.get("note") or ""
            weight_id = weight.get("weight_id", "")

            print(
                f"{date_str:<20} {weight_kg:<15.2f} {weight_g:<12} {note[:38]:<40} {weight_id[:23]:<25}"
            )

        print("=" * 100)
        print(f"總共 {len(weights)} 筆記錄")


def main() -> None:
    """主函數."""
    parser = argparse.ArgumentParser(
        description="批次體重記錄工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    subparsers = parser.add_subparsers(dest="command", help="指令")

    # Import 指令
    import_parser = subparsers.add_parser("import", help="從 CSV 批次匯入體重記錄")
    import_parser.add_argument("--baby-id", required=True, help="嬰兒 ID")
    import_parser.add_argument("--email", required=True, help="帳號（Email）")
    import_parser.add_argument("--password", required=True, help="密碼")
    import_parser.add_argument("--csv-path", required=True, help="CSV 檔案路徑")

    # Query 指令
    query_parser = subparsers.add_parser("query", help="批次查詢體重記錄")
    query_parser.add_argument("--baby-id", required=True, help="嬰兒 ID")
    query_parser.add_argument("--email", required=True, help="帳號（Email）")
    query_parser.add_argument("--password", required=True, help="密碼")
    query_parser.add_argument("--from-date", help="起始日期 (YYYY-MM-DD)")
    query_parser.add_argument("--to-date", help="結束日期 (YYYY-MM-DD)")
    query_parser.add_argument(
        "--format", choices=["table", "json"], default="table", help="輸出格式 (預設: table)"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "import":
        import_from_csv(args.baby_id, args.email, args.password, args.csv_path)
    elif args.command == "query":
        from_date = datetime.strptime(args.from_date, "%Y-%m-%d").date() if args.from_date else None
        to_date = datetime.strptime(args.to_date, "%Y-%m-%d").date() if args.to_date else None
        query_weights(args.baby_id, args.email, args.password, from_date, to_date, args.format)


if __name__ == "__main__":
    main()
