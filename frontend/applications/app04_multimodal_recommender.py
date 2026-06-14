"""Application 04 frontend: multimodal product recommendation."""

from __future__ import annotations

import streamlit as st

from core.components import product_selector, show_query_product, show_results
from src.applications.backend import ApplicationBackend
from src.common.models import Product


def render(
    backend: ApplicationBackend,
    products: list[Product],
) -> None:
    st.header("Aplicacion 04: Recomendacion multimodal")
    st.write("Combina el texto y la imagen del producto seleccionado.")
    engine = st.radio(
        "Motor de recuperacion",
        ("Implementacion propia", "PostgreSQL GIN + pgvector HNSW"),
        horizontal=True,
    )
    product = product_selector("Producto de referencia", products, "multimodal_product")
    top_k = st.slider("Cantidad de recomendaciones", 1, 12, 6)
    show_query_product(product)
    if st.button("Recomendar productos relacionados", type="primary"):
        recommender = (
            backend.multimodal_recommender_postgres
            if engine.startswith("PostgreSQL")
            else backend.multimodal_recommender
        )
        if recommender is None:
            st.error("El motor PostgreSQL multimodal no esta configurado.")
            return
        with st.spinner("Fusionando resultados textuales y visuales..."):
            show_results(
                recommender.recommend(
                    product_id=product.product_id,
                    top_k=top_k,
                )
            )
