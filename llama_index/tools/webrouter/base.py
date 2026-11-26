"""WebRouter tool spec."""

import logging

from llama_index.core.schema import Document
from llama_index.core.tools.tool_spec.base import BaseToolSpec

logger = logging.getLogger(__name__)


class WebRouterToolSpec(BaseToolSpec):
    """
    WebRouter tool spec.

    Web search and page extraction through WebRouter, which sends each call to
    one of several providers and falls back to the next if that call fails.
    No API key is needed. A provider key set in the environment, such as
    TAVILY_API_KEY, EXA_API_KEY or FIRECRAWL_API_KEY, adds that provider to
    the routing, and the calls it serves are billed to that key.
    """

    spec_functions = [
        "search",
        "extract",
    ]

    def __init__(
        self,
        search_provider: str | None = None,
        extract_provider: str | None = None,
    ) -> None:
        """
        Initialize with parameters.

        Args:
            search_provider: Send every search to this provider, e.g. "tavily".
                None lets WebRouter pick one and fall back.
            extract_provider: Send every extract to this provider, e.g.
                "firecrawl". None lets WebRouter pick one and fall back.

        """
        from web_router import WebRouter

        self.router = WebRouter()
        self.search_provider = search_provider
        self.extract_provider = extract_provider

    def search(
        self,
        query: str,
        max_results: int = 5,
        include_domains: list[str] | None = None,
    ) -> list[Document]:
        """
        Search the web and return ranked results.

        Args:
            query: What to search the web for.
            max_results: How many results to return.
            include_domains: Only return results from these domains, e.g. ["docs.python.org"].

        Returns:
            A list of Documents, one per result, with the result's text and its
            url, title and the provider that served it in the metadata.

        """
        response = self.router.search(
            query,
            provider=self.search_provider,
            max_results=max_results,
            include_domains=include_domains,
            data_apis=False,
        )
        return [
            Document(
                text=result.content or result.description,
                metadata={
                    "url": result.url,
                    "title": result.title,
                    "published_date": result.published_date,
                    "provider": response.provider,
                },
            )
            for result in response.results
        ]

    def extract(self, urls: list[str]) -> list[Document]:
        """
        Read web pages and return their main content as markdown.

        Args:
            urls: The http(s) URLs to read.

        Returns:
            A list of Documents, one per page that could be read, with the page
            content and its url, title and the provider that served it in the
            metadata. URLs that could not be read are logged and left out.

        """
        response = self.router.extract(
            urls,
            provider=self.extract_provider,
            format="markdown",
            data_apis=False,
        )
        for failure in response.failures:
            logger.warning(
                "WebRouter could not read %s: %s", failure.url, failure.error
            )
        return [
            Document(
                text=document.content,
                metadata={
                    "url": document.url,
                    "title": document.title,
                    "provider": response.provider,
                },
            )
            for document in response.documents
        ]
