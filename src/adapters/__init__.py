"""Backend adapters used by task-driven logic."""

from .base_hand_adapter import (
    BaseHandAdapter,
    ContactSummary,
    HandClosureSummary,
    JointStateSummary,
    PoseState,
    RelativePoseState,
)
from .shadow_hand_adapter import ShadowHandAdapter


def create_hand_adapter(env):
    """Create the best available adapter for the current runtime backend."""
    if env.__class__.__name__ == "ShadowGraspEnv":
        return ShadowHandAdapter(env)
    raise ValueError(f"No hand adapter registered for env type: {env.__class__.__name__}")


__all__ = [
    "BaseHandAdapter",
    "PoseState",
    "RelativePoseState",
    "JointStateSummary",
    "ContactSummary",
    "HandClosureSummary",
    "ShadowHandAdapter",
    "create_hand_adapter",
]
