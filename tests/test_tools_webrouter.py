import logging
from unittest.mock import patch

import pytest
from llama_index.core.schema import Document
from llama_index.core.tools.tool_spec.base import BaseToolSpec
from web_router.types import (
    ExtractedDocument,
    ExtractResponse,
    SearchResponse,
    SearchResult,
)
from web_router.types_errors import ExtractFailure

from llama_index.tools.webrouter import WebRouterToolSpec


@pytest.fixture
def router():
    with patch("web_router.WebRouter") as mock_router_class:
        yield mock_router_class.return_value


def test_class():
    names_of_base_classes = [b.__name__ for b in WebRouterToolSpec.__mro__]
    assert BaseToolSpec.__name__ in names_of_base_classes


def test_spec_functions():
    assert WebRouterToolSpec.spec_functions == ["search", "extract"]


def test_to_tool_list(router):
    tools = WebRouterToolSpec().to_tool_list()

    assert [tool.metadata.name for tool in tools] == ["search", "extract"]


def test_search(router):
    router.search.return_value = SearchResponse(
        provider="duckduckgo",
        query="llamaindex",
        results=[
            SearchResult(
                url="https://example1.com",
                title="Example 1",
                description="Snippet 1",
                content="Full text 1",
                published_date="2026-01-01",
            ),
            SearchResult(url="https://example2.com", description="Snippet 2"),
        ],
    )

    results = WebRouterToolSpec().search("llamaindex", max_results=2)

    router.search.assert_called_once_with(
        "llamaindex",
        provider=None,
        max_results=2,
        include_domains=None,
        data_apis=False,
    )
    assert all(isinstance(doc, Document) for doc in results)
    assert results[0].text == "Full text 1"
    assert results[0].metadata == {
        "url": "https://example1.com",
        "title": "Example 1",
        "published_date": "2026-01-01",
        "provider": "duckduckgo",
    }
    assert results[1].text == "Snippet 2"
    assert results[1].metadata["url"] == "https://example2.com"


def test_search_with_provider_and_domains(router):
    router.search.return_value = SearchResponse(provider="tavily", query="q")
    tool = WebRouterToolSpec(search_provider="tavily")

    results = tool.search("q", include_domains=["docs.python.org"])

    router.search.assert_called_once_with(
        "q",
        provider="tavily",
        max_results=5,
        include_domains=["docs.python.org"],
        data_apis=False,
    )
    assert results == []


def test_extract(router):
    router.extract.return_value = ExtractResponse(
        provider="jina",
        documents=[
            ExtractedDocument(
                url="https://example1.com", title="Example 1", content="# Page 1"
            ),
        ],
    )
    tool = WebRouterToolSpec(extract_provider="jina")

    results = tool.extract(["https://example1.com"])

    router.extract.assert_called_once_with(
        ["https://example1.com"],
        provider="jina",
        format="markdown",
        data_apis=False,
    )
    assert len(results) == 1
    assert results[0].text == "# Page 1"
    assert results[0].metadata == {
        "url": "https://example1.com",
        "title": "Example 1",
        "provider": "jina",
    }


def test_extract_logs_failures(router, caplog):
    router.extract.return_value = ExtractResponse(
        provider="jina",
        documents=[ExtractedDocument(url="https://example1.com", content="Page 1")],
        failures=[ExtractFailure(url="https://example2.com", error="HTTP 404")],
    )

    with caplog.at_level(logging.WARNING):
        results = WebRouterToolSpec().extract(
            ["https://example1.com", "https://example2.com"]
        )

    assert [doc.metadata["url"] for doc in results] == ["https://example1.com"]
    assert "https://example2.com: HTTP 404" in caplog.text
