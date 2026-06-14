"""Reusable Streamlit components shared by frontend applications."""

from __future__ import annotations

import streamlit as st

# Importing runtime initializes the backend source path for standalone imports.
from core import runtime as _runtime
from src.common.models import Product, SearchResult
from src.presentation.presentation import format_product_option, result_summary


def show_query_product(product: Product) -> None:
    left, right = st.columns([1, 2])
    with left:
        if product.image_path:
            st.image(str(product.image_path), caption=f"Producto {product.product_id}")
    with right:
        st.subheader(product.metadata.get("product_display_name", "Producto"))
        st.write(f"**ID:** {product.product_id}")
        st.write(f"**Tipo:** {product.categories.get('articleType', '')}")
        st.write(f"**Color:** {product.categories.get('baseColour', '')}")
        st.write(f"**Uso:** {product.categories.get('usage', '')}")


def show_results(results: list[SearchResult]) -> None:
    if not results:
        st.warning("No se encontraron resultados.")
        return

    st.subheader("Resultados")
    columns_per_row = 3
    for start in range(0, len(results), columns_per_row):
        columns = st.columns(columns_per_row)
        for column, result in zip(columns, results[start : start + columns_per_row]):
            summary = result_summary(result)
            with column:
                if summary["image_path"]:
                    st.image(str(summary["image_path"]), use_container_width=True)
                st.markdown(f"**#{summary['rank']} - {summary['name']}**")
                st.caption(
                    f"ID {summary['product_id']} | "
                    f"{summary['article_type']} | {summary['color']}"
                )
                st.metric("Score", summary["score"])
                if summary["text_score"] is not None:
                    st.caption(
                        f"Texto: {summary['text_score']} | "
                        f"Imagen: {summary['image_score']}"
                    )


def product_selector(label: str, products: list[Product], key: str) -> Product:
    by_id = {product.product_id: product for product in products}
    selected_id = st.selectbox(
        label,
        options=list(by_id),
        format_func=lambda product_id: format_product_option(by_id[product_id]),
        key=key,
    )
    return by_id[selected_id]
