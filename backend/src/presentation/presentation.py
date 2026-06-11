"""Presentation helpers independent from the Streamlit runtime."""

from __future__ import annotations

from src.common.models import Product, SearchResult


def format_product_option(product: Product) -> str:
    name = product.metadata.get("product_display_name") or "Producto sin nombre"
    article_type = product.categories.get("articleType", "Sin categoria")
    return f"{product.product_id} | {name} | {article_type}"


def result_summary(result: SearchResult) -> dict[str, str | float | int | None]:
    categories = result.metadata.get("categories", {})
    modality_scores = result.metadata.get("modality_scores", {})
    return {
        "rank": result.rank,
        "product_id": result.product_id,
        "name": result.metadata.get("product_display_name", ""),
        "article_type": categories.get("articleType", ""),
        "color": categories.get("baseColour", ""),
        "score": round(result.score, 4),
        "text_score": round(modality_scores["text"], 4)
        if "text" in modality_scores
        else None,
        "image_score": round(modality_scores["image"], 4)
        if "image" in modality_scores
        else None,
        "image_path": result.metadata.get("image_path"),
    }
