"""Central filesystem locations for the financial planner.

Every data location is derived from a single root so that a deployment can keep
planning data outside the repository. Set ``FP_DATA_DIR`` to an absolute path to
relocate raw inputs, scenarios, and the login audit log together; when it is
unset the bundled ``data/`` directory is used, which is the mock-data default
used for development and tests.

Note that this module intentionally does not call ``load_dotenv()``. The API
loads the environment in ``api.main`` before importing anything that reads these
constants, while test runs deliberately fall back to the repository default so
that a populated ``.env`` can never point a test run at production data.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]

_DATA_DIR_ENV: Final[str | None] = os.environ.get("FP_DATA_DIR")

DATA_DIR: Final[Path] = (
    Path(_DATA_DIR_ENV).expanduser().resolve()
    if _DATA_DIR_ENV
    else PROJECT_ROOT / "data"
)

RAW_DIR: Final[Path] = DATA_DIR / "raw"
SCENARIOS_DIR: Final[Path] = DATA_DIR / "scenarios"
LOGIN_AUDIT_LOG: Final[Path] = DATA_DIR / "login_audit.log"
