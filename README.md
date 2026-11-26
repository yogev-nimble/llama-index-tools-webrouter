# WebRouter Tool

[WebRouter](https://github.com/Nimbleway/webrouter) is an open-source (Apache-2.0) Python library that puts one interface in front of several web search and extraction providers. Each call goes to one provider and falls back to the next if that call fails.

**No API key is needed.** With no key set, calls go to providers that work without one. A provider key set in the environment, such as `TAVILY_API_KEY`, `EXA_API_KEY` or `FIRECRAWL_API_KEY`, adds that provider to the routing, and the calls it serves are billed to that key. The [WebRouter docs](https://docs.webrouter.net) list the providers and their variables.

WebRouter needs Python 3.11 or later.

## Installation

```bash
pip install llama-index-tools-webrouter
```

## Usage

```python
from llama_index.tools.webrouter import WebRouterToolSpec
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.openai import OpenAI

webrouter_tool = WebRouterToolSpec()
agent = FunctionAgent(
    tools=webrouter_tool.to_tool_list(),
    llm=OpenAI(model="gpt-4o"),
)

await agent.run("What changed in the latest Python release? Read the release notes.")
```

To send every call to one provider instead of letting WebRouter pick, name it:

```python
webrouter_tool = WebRouterToolSpec(
    search_provider="tavily", extract_provider="firecrawl"
)
```

## Available Functions

`search`: Search the web for a query. Returns a list of Documents, one per result, with the result's text and its `url`, `title`, `published_date` and the `provider` that served it in the metadata. `max_results` sets how many results come back, and `include_domains` limits them to given domains.

`extract`: Read one or more URLs. Returns a list of Documents, one per page, with the page content as markdown and its `url`, `title` and `provider` in the metadata. URLs that could not be read are logged as warnings and left out.

The functions can also be called directly:

```python
from llama_index.tools.webrouter import WebRouterToolSpec

webrouter_tool = WebRouterToolSpec()

for doc in webrouter_tool.search("LlamaIndex agents", max_results=3):
    print(doc.metadata["title"], doc.metadata["url"])

pages = webrouter_tool.extract(["https://docs.llamaindex.ai/"])
print(pages[0].text[:500])
```

This loader is designed to be used as a way to load data as a Tool in an Agent.

## Development

```bash
pip install -e ".[test]"
ruff check . && ruff format --check .
mypy llama_index
pytest
```

The tests mock WebRouter and run offline. [examples/webrouter.ipynb](examples/webrouter.ipynb) runs the tools live; search and extract need no key, the agent cell needs an LLM key.

## Support and license

This package is maintained by the WebRouter maintainers. Report problems in this repository's [issues](https://github.com/yogev-nimble/llama-index-tools-webrouter/issues). Licensed under Apache-2.0.
