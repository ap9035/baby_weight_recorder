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
    WeightAssessment,
    WeightCreate,
    WeightResponse,
    WeightUpdate,
)
from api.app.services import AssessmentService

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
    baby_repo: BabyRepoDep,
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

    # 如果需要評估，取得嬰兒資料
    baby = None
    if include_assessment:
        baby = await baby_repo.get(baby_id)

    results = []
    for w in weights:
        assessment = None
        if include_assessment and baby:
            assessment = AssessmentService.assess_weight_brief(
                weight_g=w.weight_g,
                gender=baby.gender.value,  # type: ignore
                birth_date=baby.birth_date,
                measure_date=w.timestamp.date(),
            )

        results.append(
            WeightResponse(
                weight_id=w.weight_id,
                baby_id=w.baby_id,
                timestamp=w.timestamp,
                weight_g=w.weight_g,
                note=w.note,
                created_by=w.created_by,
                created_at=w.created_at,
                updated_at=w.updated_at,
                assessment=assessment,
            )
        )

    return results


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


@router.get(
    "/{weight_id}/assessment",
    response_model=WeightAssessment,
    summary="取得體重成長評估",
)
async def get_weight_assessment(
    baby_id: str,
    weight_id: str,
    current_user: CurrentUserDep,
    baby_repo: BabyRepoDep,
    weight_repo: WeightRepoDep,
    membership: Annotated[Membership, Depends(require_baby_membership)],
) -> WeightAssessment:
    """取得單筆體重的成長曲線評估.
    
    基於 WHO 兒童生長標準 (台灣採用)，評估嬰兒體重在同齡同性別中的百分位。
    
    - **percentile**: 百分位數 (0-100)
    - **z_score**: Z 分數 (標準差)
    - **assessment**: 評估結果
        - `severely_underweight`: 體重嚴重不足 (< P3)
        - `underweight`: 體重偏低 (P3-P15)
        - `normal`: 正常範圍 (P15-P85)
        - `overweight`: 體重偏高 (P85-P97)
        - `severely_overweight`: 體重過重 (> P97)
    - **reference_range**: 該月齡的參考體重範圍 (P3/P15/P50/P85/P97)
    
    注意：目前支援 0-24 個月的嬰兒。超出範圍會回傳 400 錯誤。
    """
    # 取得體重紀錄
    weight = await weight_repo.get(baby_id, weight_id)
    if not weight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Weight record not found",
        )

    # 取得嬰兒資料
    baby = await baby_repo.get(baby_id)
    if not baby:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Baby not found",
        )

    # 計算評估
    assessment = AssessmentService.assess_weight(
        weight_id=weight.weight_id,
        weight_g=weight.weight_g,
        gender=baby.gender.value,  # type: ignore
        birth_date=baby.birth_date,
        measure_date=weight.timestamp.date(),
    )

    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot assess: age out of range (0-24 months supported)",
        )

    return assessment
