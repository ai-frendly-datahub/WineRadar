"""Re-export collector functions from radar-core.

This module provides a thin wrapper around radar-core's collector functionality.
All actual collection logic is maintained in the shared radar-core library.
"""

from __future__ import annotations

from radar_core.collector import (
    RateLimiter,
    collect_sources,
)


__all__ = ["RateLimiter", "collect_sources"]
