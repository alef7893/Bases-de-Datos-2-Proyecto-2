CREATE TABLE IF NOT EXISTS products (
    product_id BIGINT PRIMARY KEY,
    canonical_text TEXT NOT NULL,
    image_path TEXT,
    categories JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    has_image BOOLEAN NOT NULL,
    has_description BOOLEAN NOT NULL,
    duplicate_image_group TEXT
);

CREATE TABLE IF NOT EXISTS dataset_memberships (
    scale TEXT NOT NULL,
    split TEXT NOT NULL CHECK (split IN ('train', 'validation', 'test')),
    product_id BIGINT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    PRIMARY KEY (scale, product_id)
);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    product_id BIGINT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    modality TEXT NOT NULL,
    position INTEGER NOT NULL CHECK (position >= 0),
    content TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS codebooks (
    codebook_id TEXT PRIMARY KEY,
    modality TEXT NOT NULL,
    scale TEXT NOT NULL,
    size INTEGER NOT NULL CHECK (size > 0),
    artifact_path TEXT NOT NULL,
    parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS codebook_entries (
    codebook_id TEXT NOT NULL REFERENCES codebooks(codebook_id) ON DELETE CASCADE,
    codeword_id TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    centroid vector(128),
    PRIMARY KEY (codebook_id, codeword_id)
);

CREATE TABLE IF NOT EXISTS histograms (
    histogram_id TEXT PRIMARY KEY,
    product_id BIGINT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    chunk_id TEXT REFERENCES chunks(chunk_id) ON DELETE CASCADE,
    modality TEXT NOT NULL,
    scale TEXT NOT NULL,
    codebook_id TEXT NOT NULL REFERENCES codebooks(codebook_id),
    sparse_values JSONB NOT NULL DEFAULT '{}'::jsonb,
    visual_vector vector(512),
    UNIQUE (scale, modality, product_id, chunk_id)
);

CREATE TABLE IF NOT EXISTS postings (
    modality TEXT NOT NULL,
    scale TEXT NOT NULL,
    codeword_id TEXT NOT NULL,
    item_id TEXT NOT NULL,
    product_id BIGINT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    weight DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (modality, scale, codeword_id, item_id)
);

CREATE TABLE IF NOT EXISTS experiment_runs (
    run_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    scale TEXT NOT NULL,
    seed INTEGER NOT NULL,
    status TEXT NOT NULL,
    parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS dataset_memberships_split_idx
    ON dataset_memberships (scale, split);

CREATE INDEX IF NOT EXISTS chunks_product_modality_idx
    ON chunks (product_id, modality);

CREATE INDEX IF NOT EXISTS histograms_product_modality_idx
    ON histograms (product_id, modality, scale);

CREATE INDEX IF NOT EXISTS postings_lookup_idx
    ON postings (modality, scale, codeword_id);
