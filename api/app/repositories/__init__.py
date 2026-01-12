"""Repositories."""

from api.app.repositories.base import (
    BabyRepository,
    IdentityLinkRepository,
    MembershipRepository,
    UserRepository,
    WeightRepository,
)
from api.app.repositories.firestore import (
    FirestoreBabyRepository,
    FirestoreIdentityLinkRepository,
    FirestoreMembershipRepository,
    FirestoreRepositories,
    FirestoreUserRepository,
    FirestoreWeightRepository,
)
from api.app.repositories.memory import (
    InMemoryBabyRepository,
    InMemoryIdentityLinkRepository,
    InMemoryMembershipRepository,
    InMemoryRepositories,
    InMemoryUserRepository,
    InMemoryWeightRepository,
)

__all__ = [
    # Base interfaces
    "IdentityLinkRepository",
    "UserRepository",
    "BabyRepository",
    "MembershipRepository",
    "WeightRepository",
    # In-Memory implementations
    "InMemoryIdentityLinkRepository",
    "InMemoryUserRepository",
    "InMemoryBabyRepository",
    "InMemoryMembershipRepository",
    "InMemoryWeightRepository",
    "InMemoryRepositories",
    # Firestore implementations
    "FirestoreIdentityLinkRepository",
    "FirestoreUserRepository",
    "FirestoreBabyRepository",
    "FirestoreMembershipRepository",
    "FirestoreWeightRepository",
    "FirestoreRepositories",
]
