"""Vision-side helpers for deployable palm observation experiments."""

from .palm_landmarks import (
    PALM_FEATURE_DIM,
    build_palm_feature,
    extract_landmarks_from_json_frame,
    frames_to_arrays,
    summarize_palm_trace,
    validate_landmarks,
)
from .hand_open_close import (
    OPEN_CLOSE_FEATURE_DIM,
    OPEN_CLOSE_FEATURE_NAMES,
    build_open_close_feature,
    estimate_active_segment,
    open_close_features_from_landmarks,
    summarize_open_close_features,
)
from .shadow_retarget import (
    SHADOW_ACTUATOR_NAMES,
    RetargetConfig,
    action_summary,
    config_to_metadata,
    retarget_landmark_sequence,
    retarget_landmarks_to_shadow_action,
)

__all__ = [
    "PALM_FEATURE_DIM",
    "OPEN_CLOSE_FEATURE_DIM",
    "OPEN_CLOSE_FEATURE_NAMES",
    "SHADOW_ACTUATOR_NAMES",
    "RetargetConfig",
    "action_summary",
    "config_to_metadata",
    "build_open_close_feature",
    "build_palm_feature",
    "estimate_active_segment",
    "extract_landmarks_from_json_frame",
    "frames_to_arrays",
    "open_close_features_from_landmarks",
    "retarget_landmark_sequence",
    "retarget_landmarks_to_shadow_action",
    "summarize_open_close_features",
    "summarize_palm_trace",
    "validate_landmarks",
]
