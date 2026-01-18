"""嬰兒 API 路由."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.app.dependencies import (
    BabyRepoDep,
    CurrentUserDep,
    MembershipRepoDep,
    require_baby_membership,
    require_baby_write_access,
)
from api.app.models import (
    BabyCreate,
    BabyCreateResponse,
    BabyResponse,
    BabyUpdate,
    MemberRole,
    Membership,
)

router = APIRouter(prefix="/v1/babies", tags=["Babies"])


@router.post(
    "",
    response_model=BabyCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="建立嬰兒",
)
async def create_baby(
    data: BabyCreate,
    current_user: CurrentUserDep,
    baby_repo: BabyRepoDep,
    membership_repo: MembershipRepoDep,
) -> BabyCreateResponse:
    """建立新嬰兒。

    建立者會自動成為 owner。
    """
    if not current_user.internal_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not registered",
        )

    # 建立嬰兒
    baby = await baby_repo.create(data)

    # 建立 owner membership
    await membership_repo.create(
        baby_id=baby.baby_id,
        internal_user_id=current_user.internal_user_id,
        role=MemberRole.OWNER,
    )

    return BabyCreateResponse(baby_id=baby.baby_id)


@router.get(
    "",
    response_model=list[BabyResponse],
    summary="列出嬰兒",
)
async def list_babies(
    current_user: CurrentUserDep,
    baby_repo: BabyRepoDep,
    membership_repo: MembershipRepoDep,
) -> list[BabyResponse]:
    """列出當前使用者可存取的所有嬰兒。"""
    if not current_user.internal_user_id:
        return []

    # 取得使用者的所有成員資格
    memberships = await membership_repo.list_by_user(current_user.internal_user_id)
    membership_map = {m.baby_id: m for m in memberships}

    # 取得嬰兒列表
    babies = await baby_repo.list_by_user(current_user.internal_user_id)

    # 組合回應
    return [
        BabyResponse(
            baby_id=baby.baby_id,
            name=baby.name,
            birth_date=baby.birth_date,
            gender=baby.gender,
            created_at=baby.created_at,
            role=membership_map[baby.baby_id].role.value
            if baby.baby_id in membership_map
            else None,
        )
        for baby in babies
    ]


@router.get(
    "/{baby_id}",
    response_model=BabyResponse,
    summary="取得嬰兒",
)
async def get_baby(
    baby_id: str,
    current_user: CurrentUserDep,
    baby_repo: BabyRepoDep,
    membership: Annotated[Membership, Depends(require_baby_membership)],
) -> BabyResponse:
    """取得單一嬰兒資料。"""
    baby = await baby_repo.get(baby_id)
    if not baby:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Baby not found",
        )

    return BabyResponse(
        baby_id=baby.baby_id,
        name=baby.name,
        birth_date=baby.birth_date,
        gender=baby.gender,
        created_at=baby.created_at,
        role=membership.role.value,
    )


@router.get(
    "/{baby_id}/growth-curve",
    summary="取得 WHO 生長曲線參考數據",
)
async def get_growth_curve(
    baby_id: str,
    from_month: int = Query(0, ge=0, le=60, description="起始月齡 (0-60)"),
    to_month: int = Query(60, ge=0, le=60, description="結束月齡 (0-60)"),
    current_user: CurrentUserDep = Depends(),
    baby_repo: BabyRepoDep = Depends(),
    membership: Annotated[Membership, Depends(require_baby_membership)] = None,
) -> dict:
    """取得 WHO 生長曲線參考數據（P3, P15, P50, P85, P97）.

    返回指定月齡範圍內各百分位的體重參考值，用於繪製生長曲線圖。

    Args:
        baby_id: 嬰兒 ID
        from_month: 起始月齡 (0-60)
        to_month: 結束月齡 (0-60)

    Returns:
        {
            "gender": "male" | "female",
            "birth_date": "YYYY-MM-DD",
            "curve_data": [
                {
                    "age_months": 0,
                    "p3": 2.5,
                    "p15": 2.9,
                    "p50": 3.3,
                    "p85": 3.8,
                    "p97": 4.2
                },
                ...
            ]
        }
    """
    from api.app.data import get_percentile_weights

    # 取得嬰兒資料
    baby = await baby_repo.get(baby_id)
    if not baby:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Baby not found",
        )

    # 驗證月齡範圍
    if from_month > to_month:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="from_month must be <= to_month",
        )

    # 取得生長曲線數據
    curve_data = []
    for age in range(from_month, min(to_month + 1, 61)):  # 最多到 60 個月
        percentile_weights = get_percentile_weights(
            gender=baby.gender.value,  # type: ignore
            age_months=age,
        )
        if percentile_weights:
            curve_data.append(
                {
                    "age_months": age,
                    "p3": percentile_weights[3],
                    "p15": percentile_weights[15],
                    "p50": percentile_weights[50],
                    "p85": percentile_weights[85],
                    "p97": percentile_weights[97],
                }
            )

    return {
        "gender": baby.gender.value,  # type: ignore
        "birth_date": baby.birth_date.isoformat(),
        "curve_data": curve_data,
    }


@router.put(
    "/{baby_id}",
    response_model=BabyResponse,
    summary="更新嬰兒",
)
async def update_baby(
    baby_id: str,
    data: BabyUpdate,
    current_user: CurrentUserDep,
    baby_repo: BabyRepoDep,
    membership: Annotated[Membership, Depends(require_baby_write_access)],
) -> BabyResponse:
    """更新嬰兒資料。需要 owner 或 editor 權限。"""
    baby = await baby_repo.update(baby_id, data)
    if not baby:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Baby not found",
        )

    return BabyResponse(
        baby_id=baby.baby_id,
        name=baby.name,
        birth_date=baby.birth_date,
        gender=baby.gender,
        created_at=baby.created_at,
        role=membership.role.value,
    )


@router.delete(
    "/{baby_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="刪除嬰兒",
)
async def delete_baby(
    baby_id: str,
    current_user: CurrentUserDep,
    baby_repo: BabyRepoDep,
    membership: Annotated[Membership, Depends(require_baby_membership)],
) -> None:
    """刪除嬰兒。只有 owner 可以刪除。"""
    if not membership.can_manage():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner can delete baby",
        )

    deleted = await baby_repo.delete(baby_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Baby not found",
        )
