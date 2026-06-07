"""One-off: fix checko/ and pipeline/ packages with proper cross-imports."""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git_text(path: str) -> str:
    return subprocess.check_output(
        ["git", "show", f"HEAD:backend/{path}"],
        cwd=ROOT.parent,
        text=True,
        encoding="utf-8",
    )


def slice_lines(text: str, start: int, end: int) -> str:
    lines = text.splitlines(keepends=True)
    return "".join(lines[start - 1 : end])


def write_checko() -> None:
    src = git_text("leadgen/modules/checko.py")
    pkg = ROOT / "leadgen" / "modules" / "checko"
    pkg.mkdir(parents=True, exist_ok=True)

    cache_body = slice_lines(src, 36, 133)
    http_body = slice_lines(src, 135, 186)
    search_body = slice_lines(src, 195, 356)
    parse_body = slice_lines(src, 357, 582)
    endpoints_body = slice_lines(src, 583, 936)
    person_body = slice_lines(src, 937, 1033)
    helpers_body = slice_lines(src, 1034, 1115)

    (pkg / "cache.py").write_text(
        '''"""Checko cache and circuit breaker."""
from __future__ import annotations

import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

'''
        + cache_body
        + "\n_cache_load()\n",
        encoding="utf-8",
    )

    (pkg / "http_client.py").write_text(
        '''"""Checko HTTP client."""
from __future__ import annotations

import logging
import os

import httpx

from .cache import (
    BASE,
    TIMEOUT,
    _breaker_is_open,
    _breaker_record_forbidden,
    _breaker_record_success,
    _cache_get,
    _cache_key,
    _cache_put,
)

logger = logging.getLogger(__name__)

'''
        + http_body
        + "\n",
        encoding="utf-8",
    )

    (pkg / "helpers.py").write_text(
        '''"""Checko parsing helpers."""
from __future__ import annotations

import re
from typing import Any

'''
        + helpers_body
        + "\n",
        encoding="utf-8",
    )

    (pkg / "parse_company.py").write_text(
        '''"""Checko company response parsing."""
from __future__ import annotations

from .helpers import (
    _clean_city,
    _detect_mgt,
    _num,
    _parse_status,
)

'''
        + parse_body
        + "\n",
        encoding="utf-8",
    )

    (pkg / "search.py").write_text(
        '''"""Checko company search."""
from __future__ import annotations

import logging
import re

import httpx

from .helpers import _extract_city, _parse_status, _str_from_field
from .http_client import _available, _get
from .parse_company import _parse_company

logger = logging.getLogger(__name__)

'''
        + search_body
        + "\n",
        encoding="utf-8",
    )

    (pkg / "endpoints.py").write_text(
        '''"""Checko API endpoints (finances, legal, profile)."""
from __future__ import annotations

import logging
from typing import Any

from .http_client import _get

logger = logging.getLogger(__name__)

'''
        + endpoints_body
        + "\n",
        encoding="utf-8",
    )

    (pkg / "person.py").write_text(
        '''"""Checko person lookup."""
from __future__ import annotations

import logging
from typing import Any

from .helpers import (
    _clean_city,
    _detect_mgt,
    _extract_city,
    _num,
    _parse_status,
    _str_from_field,
    _sum_num,
)
from .http_client import _get

logger = logging.getLogger(__name__)

'''
        + person_body
        + "\n",
        encoding="utf-8",
    )

    (pkg / "__init__.py").write_text(
        '''"""Checko.ru API client package."""
from .endpoints import (
    fetch_bankruptcy,
    fetch_contracts,
    fetch_enforcements,
    fetch_fedresurs,
    fetch_finances,
    fetch_full_profile,
    fetch_inspections,
    fetch_legal_cases,
    _parse_finances,
)
from .cache import get_runtime_state
from .helpers import _num, _parse_status
from .http_client import _available
from .parse_company import _parse_company
from .person import fetch_person
from .search import fetch_company, search_companies

__all__ = [
    "fetch_company",
    "search_companies",
    "fetch_finances",
    "fetch_legal_cases",
    "fetch_enforcements",
    "fetch_contracts",
    "fetch_bankruptcy",
    "fetch_inspections",
    "fetch_fedresurs",
    "fetch_full_profile",
    "fetch_person",
    "get_runtime_state",
    "_parse_company",
    "_parse_status",
    "_parse_finances",
    "_num",
    "_available",
]
''',
        encoding="utf-8",
    )


def write_pipeline() -> None:
    src = git_text("leadgen/pipeline.py")
    pkg = ROOT / "leadgen" / "pipeline"
    pkg.mkdir(parents=True, exist_ok=True)

    portrait_cache_body = slice_lines(src, 24, 70)
    run_pipeline_body = slice_lines(src, 71, 284)
    cluster_body = slice_lines(src, 285, 443)
    search_body = slice_lines(src, 444, 793)
    gather_body = slice_lines(src, 794, 998)
    score_body = slice_lines(src, 999, 1189)
    persist_body = slice_lines(src, 1190, 1279)
    portrait_helpers_body = slice_lines(src, 1280, 1767)
    utils_body = slice_lines(src, 1768, len(src.splitlines()))

    (pkg / "portrait_cache.py").write_text(
        '''"""Portrait review cache."""
from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

'''
        + portrait_cache_body
        + "\n",
        encoding="utf-8",
    )

    (pkg / "utils.py").write_text(
        '''"""Pipeline utilities."""
from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

'''
        + utils_body
        + "\n",
        encoding="utf-8",
    )

    (pkg / "portrait_helpers.py").write_text(
        '''"""Portrait search helpers."""
from __future__ import annotations

import logging
from typing import Any

from .utils import (
    _extract_employees_from_text,
    _extract_revenue_from_text,
    _parse_json_safe,
    _safe,
)

logger = logging.getLogger(__name__)

'''
        + portrait_helpers_body
        + "\n",
        encoding="utf-8",
    )

    (pkg / "score_card.py").write_text(
        '''"""Lead card scoring and assembly."""
from __future__ import annotations

import logging
from typing import Any

from .utils import _fmt_money, _render_script

logger = logging.getLogger(__name__)

'''
        + score_body
        + "\n",
        encoding="utf-8",
    )

    (pkg / "persist.py").write_text(
        '''"""Persist lead card to CRM."""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

'''
        + persist_body
        + "\n",
        encoding="utf-8",
    )

    (pkg / "gather.py").write_text(
        '''"""Parallel data gathering for pipeline."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from .utils import _safe

logger = logging.getLogger(__name__)

'''
        + gather_body
        + "\n",
        encoding="utf-8",
    )

    (pkg / "run_pipeline.py").write_text(
        '''"""Main leadgen pipeline entry."""
from __future__ import annotations

import logging
import time
from typing import Any

from .gather import _gather_all_data, _run_leadgen_agents
from .persist import _save_to_crm
from .portrait_helpers import _extract_company_from_portrait
from .score_card import _build_lead_card, _compute_final_score
from .utils import (
    _build_connections,
    _dedup_list,
    _extract_contacts_from_web,
    _extract_domain,
    _safe,
)

logger = logging.getLogger(__name__)

'''
        + run_pipeline_body
        + "\n",
        encoding="utf-8",
    )

    (pkg / "cluster.py").write_text(
        '''"""Cluster search around anchor INN."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from .utils import _safe

logger = logging.getLogger(__name__)

'''
        + cluster_body
        + "\n",
        encoding="utf-8",
    )

    (pkg / "search_by_portrait.py").write_text(
        '''"""Portrait-based company search."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from .portrait_cache import (
    _portrait_review_cache_get,
    _portrait_review_cache_key,
    _portrait_review_cache_put,
)
from .portrait_helpers import (
    _build_portrait_seed_queries,
    _build_reference_profile,
    _dedup_companies,
    _fallback_portrait_candidates_from_web,
    _match_portrait,
    _merge_criteria_with_reference,
    _parse_portrait_criteria,
    _score_reference_similarity,
)
from .utils import _safe

logger = logging.getLogger(__name__)

'''
        + search_body
        + "\n",
        encoding="utf-8",
    )

    (pkg / "__init__.py").write_text(
        '''"""Leadgen pipeline — публичный API и re-export для тестов."""
from .cluster import run_cluster
from .gather import _build_agent_context, _gather_all_data, _run_leadgen_agents
from .persist import _save_to_crm
from .portrait_cache import (
    _portrait_review_cache_get,
    _portrait_review_cache_key,
    _portrait_review_cache_put,
)
from .portrait_helpers import (
    _build_portrait_seed_queries,
    _build_reference_profile,
    _dedup_companies,
    _extract_company_from_portrait,
    _fallback_portrait_candidates_from_web,
    _fill_missing_portrait_fields,
    _match_portrait,
    _merge_criteria_with_reference,
    _normalize_portrait_criteria,
    _parse_portrait_criteria,
    _portrait_workability_verdict,
    _score_reference_similarity,
)
from .run_pipeline import run_pipeline
from .score_card import _build_lead_card, _compute_final_score
from .search_by_portrait import _portrait_fit_analysis, search_by_portrait
from .utils import (
    _build_connections,
    _dedup_list,
    _extract_contacts_from_web,
    _extract_domain,
    _extract_employees_from_text,
    _extract_revenue_from_text,
    _fmt_money,
    _parse_json_safe,
    _render_script,
    _safe,
)

__all__ = [
    "run_pipeline",
    "run_cluster",
    "search_by_portrait",
    "_save_to_crm",
]
''',
        encoding="utf-8",
    )


def main() -> None:
    write_checko()
    write_pipeline()
    print("resplit done")


if __name__ == "__main__":
    main()
