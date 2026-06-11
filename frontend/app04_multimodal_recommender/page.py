"""Application 04 frontend: multimodal product recommendation."""

from __future__ import annotations

import streamlit as st

from shared.components import product_selector, show_query_product, show_results
from src.applications.backend import ApplicationBackend
from src.common.models import Product


def render_multimodal_recommender(
    backend: ApplicationBackend,
    products: list[Product],
) -> None:
    st.header("Aplicacion 04: Recomendacion multimodal")
    st.write("Combina el texto y la imagen del producto seleccionado.")
    product = product_selector("Producto de referencia", products, "multimodal_product")
    top_k = st.slider("Cantidad de recomendaciones", 1, 12, 6)
    show_query_product(product)
    if st.button("Recomendar productos relacionados", type="primary"):
        with st.spinner("Fusionando resultados textuales y visuales..."):
            show_results(
                backend.multimodal_recommender.recommend(
                    product_id=product.product_id,
                    top_k=top_k,
                )
            )
