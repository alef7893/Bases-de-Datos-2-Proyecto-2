from src.common.interfaces import Retriever
from src.common.models import Query


class FakeRetriever:
    def search(self, query: Query, top_k: int = 10):
        return []


def test_retriever_protocol_is_runtime_checkable() -> None:
    assert isinstance(FakeRetriever(), Retriever)
