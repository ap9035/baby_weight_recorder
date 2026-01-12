"""體重 API 路由."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.app.dependencies import (
    BabyRepoDep,
    CurrentUserDep,
    WeightRepoDep,
    require_baby_membership,
    require_baby_write_access,
)
from api.app.models import (
    Membership,
    Weight,
    WeightCreate,
    WeightResponse,
    WeightUpdate,
)

router = APIRouter(prefix="/v1/babies/{baby_id}/weights", tags=["Weights"])


@router.post(
    "",
    response_model=WeightResponse,
    status_code=status.HTTP_201_CREATED,
    summary="新增體重紀錄",
)
async def create_weight(
    baby_id: str,
    data: WeightCreate,
    current_user: CurrentUserDep,
    weight_repo: WeightRepoDep,
    membership: Annotated[Membership, Depends(require_baby_write_access)],
) -> WeightResponse:
    print(data)
    """新增體重紀錄。需要 owner 或 editor 權限。"""
    if not current_user.internal_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not registered",
        )

    weight = await weight_repo.create(
        baby_id=baby_id,
        data=data,
        created_by=current_user.internal_user_id,
    )

    return WeightResponse(
        weight_id=weight.weight_id,
        baby_id=weight.baby_id,
        timestamp=weight.timestamp,
        weight_g=weight.weight_g,
        note=weight.note,
        created_by=weight.created_by,
        created_at=weight.created_at,
        updated_at=weight.updated_at,
        assessment=None,  # TODO: 實作成長評估
    )


@router.get(
    "",
    response_model=list[WeightResponse],
    summary="查詢體重紀錄",
)
async def list_weights(
    baby_id: str,
    current_user: CurrentUserDep,
    weight_repo: WeightRepoDep,
    membership: Annotated[Membership, Depends(require_baby_membership)],
    from_date: datetime | None = Query(None, alias="from", description="起始時間"),
    to_date: datetime | None = Query(None, alias="to", description="結束時間"),
    include_assessment: bool = Query(False, description="是否包含成長評估"),
) -> list[WeightResponse]:
    """查詢體重紀錄。"""
    weights = await weight_repo.list_by_baby(
        baby_id=baby_id,
        from_date=from_date,
        to_date=to_date,
    )

    # TODO: 如果 include_assessment=True，計算成長評估
    return [
        WeightResponse(
            weight_id=w.weight_id,
            baby_id=w.baby_id,
            timestamp=w.timestamp,
            weight_g=w.weight_g,
            note=w.note,
            created_by=w.created_by,
            created_at=w.created_at,
            updated_at=w.updated_at,
            assessment=None,
        )
        for w in weights
    ]


@router.get(
    "/{weight_id}",
    response_model=WeightResponse,
    summary="取得體重紀錄",
)
async def get_weight(
    baby_id: str,
    weight_id: str,
    current_user: CurrentUserDep,
    weight_repo: WeightRepoDep,
    membership: Annotated[Membership, Depends(require_baby_membership)],
) -> WeightResponse:
    """取得單筆體重紀錄。"""
    weight = await weight_repo.get(baby_id, weight_id)
    if not weight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Weight record not found",
        )

    return WeightResponse(
        weight_id=weight.weight_id,
        baby_id=weight.baby_id,
        timestamp=weight.timestamp,
        weight_g=weight.weight_g,
        note=weight.note,
        created_by=weight.created_by,
        created_at=weight.created_at,
        updated_at=weight.updated_at,
        assessment=None,
    )


@router.put(
    "/{weight_id}",
    response_model=WeightResponse,
    summary="修改體重紀錄",
)
async def update_weight(
    baby_id: str,
    weight_id: str,
    data: WeightUpdate,
    current_user: CurrentUserDep,
    weight_repo: WeightRepoDep,
    membership: Annotated[Membership, Depends(require_baby_write_access)],
) -> WeightResponse:
    """修改體重紀錄。需要 owner 或 editor 權限。"""
    weight = await weight_repo.update(baby_id, weight_id, data)
    if not weight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Weight record not found",
        )

    return WeightResponse(
        weight_id=weight.weight_id,
        baby_id=weight.baby_id,
        timestamp=weight.timestamp,
        weight_g=weight.weight_g,
        note=weight.note,
        created_by=weight.created_by,
        created_at=weight.created_at,
        updated_at=weight.updated_at,
        assessment=None,
    )


@router.delete(
    "/{weight_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="刪除體重紀錄",
)
async def delete_weight(
    baby_id: str,
    weight_id: str,
    current_user: CurrentUserDep,
    weight_repo: WeightRepoDep,
    membership: Annotated[Membership, Depends(require_baby_write_access)],
) -> None:
    """刪除體重紀錄。需要 owner 或 editor 權限。"""
    deleted = await weight_repo.delete(baby_id, weight_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Weight record not found",
        )
