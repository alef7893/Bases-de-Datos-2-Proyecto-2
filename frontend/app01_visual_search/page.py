"""Application 01 frontend: visual e-commerce search."""

from __future__ import annotations

import streamlit as st

from shared.components import product_selector, show_query_product, show_results
from shared.runtime import save_uploaded_image
from src.applications.backend import ApplicationBackend
from src.common.models import Product


def render_visual_search(backend: ApplicationBackend, products: list[Product]) -> None:
    st.header("Aplicacion 01: Busqueda visual e-commerce")
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
                show_results(
                    backend.visual_search.search(
                        product_id=product.product_id,
                        top_k=top_k,
                    )
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
                show_results(
                    backend.visual_search.search(
                        image_path=image_path,
                        top_k=top_k,
                    )
                )
