"""嬰兒 API 路由."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

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
