---
description: Python 程式碼規範
globs: 
  - "**/*.py"
alwaysApply: false
---

# Python 開發規範

## Type Hints

所有函式必須包含完整的型別註解：

```python
def calculate_percentile(
    weight_kg: float,
    age_days: int,
    gender: Literal["male", "female"],
) -> PercentileResult:
    ...
```

## Pydantic Models

使用 Pydantic v2 語法：

```python
from pydantic import BaseModel, Field

class WeightRecord(BaseModel):
    weight_kg: float = Field(..., gt=0, description="體重（公斤）")
    recorded_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )
```

## 錯誤處理

使用 FastAPI 的 HTTPException：

```python
from fastapi import HTTPException, status

if not baby:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Baby not found",
    )
```

## 測試

- 測試檔案命名: `test_*.py`
- 使用 pytest 和 pytest-asyncio
- Mock 外部依賴（Firestore）

## 程式碼品質檢查

**在推送程式碼之前，永遠執行以下檢查（比照 CI）：**

```bash
# 1. Linter 檢查
uv run ruff check .

# 2. Format 檢查
uv run ruff format --check .
```

**自動修復：**

```bash
# 修復 linter 問題
uv run ruff check . --fix

# 修復 format 問題
uv run ruff format .
```

確保所有檢查通過後才能 `git push`。
