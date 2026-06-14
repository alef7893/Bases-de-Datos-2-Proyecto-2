"""Generic Streamlit entry point for registered frontend applications."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

FRONTEND_ROOT = Path(__file__).resolve().parent
if str(FRONTEND_ROOT) not in sys.path:
    sys.path.insert(0, str(FRONTEND_ROOT))

from applications.registry import APPLICATIONS
from core.runtime import SCALE, load_backend


def main() -> None:
    st.set_page_config(
        page_title="Proyecto 2 - Recuperacion Multimodal",
        layout="wide",
    )
    st.title("Sistema Multimodal de Recuperacion")
    st.caption(
        "Frontend funcional de pruebas para los motores propios de texto e imagen. "
        f"Escala activa: {SCALE}."
    )

    try:
        backend = load_backend()
    except Exception as error:
        st.error(f"No se pudo cargar el backend: {error}")
        st.info("Verifica que existan los indices de texto e imagen para la escala 1k.")
        st.stop()

    products = [product for product in backend.catalog.products() if product.has_image]
    tabs = st.tabs([application.label for application in APPLICATIONS])
    for tab, application in zip(tabs, APPLICATIONS, strict=True):
        with tab:
            application.render(backend, products)


if __name__ == "__main__":
    main()
