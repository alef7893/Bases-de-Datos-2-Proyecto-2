"""Shared backend loading and uploaded-file handling."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import Any

import streamlit as st

BACKEND_ROOT = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.applications.backend import ApplicationBackend, build_application_backend_with_postgres
from src.common.config import load_project_config


SCALE = "1k"


@st.cache_resource(show_spinner="Cargando indices y catalogo...")
def load_backend() -> ApplicationBackend:
    return build_application_backend_with_postgres(
        load_project_config(
            config_dir=BACKEND_ROOT / "configs",
            project_root=BACKEND_ROOT,
        ),
        scale=SCALE,
    )


def save_uploaded_image(uploaded_file: Any) -> Path:
    content = uploaded_file.getvalue()
    digest = hashlib.sha256(content).hexdigest()[:16]
    suffix = Path(uploaded_file.name).suffix.lower() or ".jpg"
    output = BACKEND_ROOT.parent / "artifacts" / "frontend_uploads" / f"{digest}{suffix}"
    output.parent.mkdir(parents=True, exist_ok=True)
    if not output.exists():
        output.write_bytes(content)
    return output.resolve()

