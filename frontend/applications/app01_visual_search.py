"""Application 01 frontend: visual e-commerce search."""

from __future__ import annotations

from time import perf_counter

import streamlit as st

from core.components import product_selector, show_query_product, show_results
from core.runtime import save_uploaded_image
from src.applications.backend import ApplicationBackend
from src.applications.app01_visual_search import VisualSearch
from src.common.models import Product


def _execute_search(visual_search: VisualSearch, **parameters) -> None:
    started = perf_counter()
    try:
        results = visual_search.search(**parameters)
    except Exception as error:
        st.error(f"No se pudo ejecutar la busqueda: {error}")
        return
    st.caption(f"Latencia total: {(perf_counter() - started) * 1000:.2f} ms")
    show_results(results)


def render(backend: ApplicationBackend, products: list[Product]) -> None:
    st.header("Aplicacion 01: Busqueda visual e-commerce")
    engine = st.selectbox(
        "Motor de busqueda",
        ["Indice invertido propio", "PostgreSQL pgvector HNSW"],
        key="visual_engine",
    )
    visual_search = (
        backend.visual_search_hnsw
        if engine == "PostgreSQL pgvector HNSW"
        else backend.visual_search
    )
    if visual_search is None:
        st.error("El motor HNSW no esta configurado.")
        return
    mode = st.radio(
        "Origen de la consulta",
        ["Producto del catalogo", "Subir imagen"],
        horizontal=True,
    )
    top_k = st.slider("Cantidad de resultados", 1, 12, 6, key="visual_top_k")

    if mode == "Producto del catalogo":
        product = product_selector("Producto consulta", products, "visual_product")
        show_query_product(product)
        if st.button("Buscar productos similares", type="primary"):
            with st.spinner("Ejecutando busqueda visual..."):
                _execute_search(
                    visual_search,
                    product_id=product.product_id,
                    top_k=top_k,
                )
        return

    uploaded = st.file_uploader(
        "Imagen consulta",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=False,
    )
    if uploaded:
        image_path = save_uploaded_image(uploaded)
        st.image(str(image_path), caption="Imagen consulta", width=300)
        if st.button("Buscar con imagen subida", type="primary"):
            with st.spinner("Ejecutando busqueda visual..."):
                _execute_search(
                    visual_search,
                    image_path=image_path,
                    top_k=top_k,
                )

