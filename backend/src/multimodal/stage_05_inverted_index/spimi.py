"""Disk-backed Single-Pass In-Memory Indexing for sparse text vectors."""

from __future__ import annotations

import heapq
import json
from collections import defaultdict
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path
from typing import Any, TextIO

from src.common.models import Chunk


class SPIMIIndexer:
    def __init__(self, output_dir: str | Path, max_postings_per_block: int = 50000):
        if max_postings_per_block <= 0:
            raise ValueError("max_postings_per_block must be positive")
        self.output_dir = Path(output_dir)
        self.blocks_dir = self.output_dir / "blocks"
        self.max_postings_per_block = max_postings_per_block

    def _write_block(
        self, block: Mapping[str, list[list[Any]]], block_number: int
    ) -> Path:
        path = self.blocks_dir / f"block-{block_number:05d}.jsonl"
        with path.open("w", encoding="utf-8", newline="\n") as stream:
            for term in sorted(block):
                stream.write(json.dumps({"term": term, "postings": block[term]}) + "\n")
        return path

    @staticmethod
    def _iter_block(stream: TextIO) -> Iterator[tuple[str, list[list[Any]]]]:
        for line in stream:
            payload = json.loads(line)
            yield payload["term"], payload["postings"]

    def _merge_blocks(self, block_paths: list[Path], output_path: Path) -> None:
        streams = [path.open("r", encoding="utf-8") for path in block_paths]
        iterators = [self._iter_block(stream) for stream in streams]
        heap: list[tuple[str, int, list[list[Any]]]] = []
        try:
            for index, iterator in enumerate(iterators):
                try:
                    term, postings = next(iterator)
                    heapq.heappush(heap, (term, index, postings))
                except StopIteration:
                    pass

            with output_path.open("w", encoding="utf-8", newline="\n") as output:
                while heap:
                    term, index, postings = heapq.heappop(heap)
                    combined = list(postings)
                    consumed = [index]
                    while heap and heap[0][0] == term:
                        _, same_index, same_postings = heapq.heappop(heap)
                        combined.extend(same_postings)
                        consumed.append(same_index)
                    combined.sort(key=lambda posting: posting[0])
                    output.write(json.dumps({"term": term, "postings": combined}) + "\n")
                    for consumed_index in consumed:
                        try:
                            next_term, next_postings = next(iterators[consumed_index])
                            heapq.heappush(
                                heap, (next_term, consumed_index, next_postings)
                            )
                        except StopIteration:
                            pass
        finally:
            for stream in streams:
                stream.close()

    def build(
        self, documents: Iterable[tuple[Chunk, Mapping[str, float]]]
    ) -> dict[str, int]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.blocks_dir.mkdir(parents=True, exist_ok=True)
        for old_block in self.blocks_dir.glob("block-*.jsonl"):
            old_block.unlink()

        block: dict[str, list[list[Any]]] = defaultdict(list)
        block_paths: list[Path] = []
        posting_count = 0
        chunk_count = 0
        metadata_path = self.output_dir / "chunks.jsonl"

        with metadata_path.open("w", encoding="utf-8", newline="\n") as metadata:
            for chunk, vector in documents:
                metadata.write(
                    json.dumps(
                        {
                            "chunk_id": chunk.chunk_id,
                            "product_id": chunk.product_id,
                            "position": chunk.position,
                        }
                    )
                    + "\n"
                )
                chunk_count += 1
                for term, weight in vector.items():
                    block[term].append([chunk.chunk_id, chunk.product_id, weight])
                    posting_count += 1
                if posting_count >= self.max_postings_per_block:
                    block_paths.append(self._write_block(block, len(block_paths)))
                    block = defaultdict(list)
                    posting_count = 0

        if block:
            block_paths.append(self._write_block(block, len(block_paths)))

        postings_path = self.output_dir / "postings.jsonl"
        self._merge_blocks(block_paths, postings_path)
        summary = {
            "chunks": chunk_count,
            "blocks": len(block_paths),
            "terms": sum(1 for _ in postings_path.open("r", encoding="utf-8")),
        }
        (self.output_dir / "summary.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )
        return summary
