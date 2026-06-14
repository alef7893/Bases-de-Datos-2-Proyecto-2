CREATE INDEX IF NOT EXISTS histograms_visual_vector_hnsw_1k_idx
    ON histograms
    USING hnsw (visual_vector vector_cosine_ops)
    WITH (m = 16, ef_construction = 64)
    WHERE modality = 'image' AND visual_vector IS NOT NULL AND scale = '1k';
