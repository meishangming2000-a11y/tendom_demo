"""Observation builders with oracle and deployable layers."""

from .deployable_observation import DeployableObservationBuilder
from .oracle_observation import OracleObservationBuilder


OBSERVATION_BUILDERS = {
    "oracle": OracleObservationBuilder,
    "deployable": DeployableObservationBuilder,
}


def get_observation_builder(mode):
    """Create an observation builder for the requested mode."""
    normalized_mode = str(mode or "oracle").strip().lower()
    if normalized_mode not in OBSERVATION_BUILDERS:
        raise ValueError(
            f"Unknown observation mode '{mode}'. Available modes: {sorted(OBSERVATION_BUILDERS.keys())}"
        )
    return OBSERVATION_BUILDERS[normalized_mode]()


__all__ = [
    "OracleObservationBuilder",
    "DeployableObservationBuilder",
    "OBSERVATION_BUILDERS",
    "get_observation_builder",
]
