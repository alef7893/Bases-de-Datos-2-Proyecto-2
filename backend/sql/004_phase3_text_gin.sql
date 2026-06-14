ALTER TABLE products
    ADD COLUMN IF NOT EXISTS search_vector tsvector
    GENERATED ALWAYS AS (
        to_tsvector('english'::regconfig, coalesce(canonical_text, ''))
    ) STORED;

CREATE INDEX IF NOT EXISTS products_search_vector_gin_idx
    ON products
    USING gin (search_vector);
