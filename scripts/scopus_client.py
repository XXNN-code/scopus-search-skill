"""Scopus API 客户端 - 封装搜索请求和分页逻辑 / Scopus API Client - Wraps search requests and pagination logic"""

import requests
from config import SCOPUS_SEARCH_URL, DEFAULT_COUNT, DEFAULT_VIEW


class ScopusAPIError(Exception):
    """Scopus API 错误基类 / Scopus API error base class"""
    pass


class ScopusAuthError(ScopusAPIError):
    """认证错误 (401) / Authentication error (401)"""
    pass


class ScopusQuotaError(ScopusAPIError):
    """配额超限错误 (429) / Quota limit exceeded error (429)"""
    pass


class ScopusClient:
    """Scopus Search API 客户端 / Scopus Search API Client"""

    def __init__(self, api_key: str):
        if not api_key:
            raise ScopusAuthError(
                "未提供 API Key。请在 .env 文件中设置 SCOPUS_API_KEY，\n"
                "或在 https://dev.elsevier.com/apikey/manage 注册获取。\n"
                "API Key not provided. Please set SCOPUS_API_KEY in the .env file,\n"
                "or register at https://dev.elsevier.com/apikey/manage."
            )
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "X-ELS-APIKey": api_key,
            "Accept": "application/json",
        })

    def search(
        self,
        query: str,
        count: int = DEFAULT_COUNT,
        start: int = 0,
        sort: str | None = None,
        view: str = DEFAULT_VIEW,
        field: str | None = None,
    ) -> dict:
        """
        执行 Scopus 搜索。
        Execute Scopus search.

        Args:
            query: Boolean 搜索表达式 / Boolean search expression, e.g. "TITLE-ABS-KEY(deep learning)"
            count: 每页结果数 (1-100) / Results per page (1-100)
            start: 起始索引 / Starting index
            sort: 排序方式 / Sort method, e.g. "-date", "+citedby-count"
            view: 视图模式 "STANDARD" 或 "COMPLETE" / View mode "STANDARD" or "COMPLETE"
            field: 返回的指定字段, 逗号分隔 / Specific fields to return, comma-separated

        Returns:
            解析后的 JSON 响应字典 / Parsed JSON response dictionary

        Raises:
            ScopusAuthError: API Key 无效或缺失 / API Key invalid or missing
            ScopusQuotaError: API 调用配额超限 / API call quota exceeded
            ScopusAPIError: 其他 API 错误 / Other API errors
        """
        params = {
            "query": query,
            "count": min(count, 100),
            "start": start,
            "view": view,
        }
        if sort:
            params["sort"] = sort
        if field:
            params["field"] = field

        response = self.session.get(SCOPUS_SEARCH_URL, params=params)
        self._handle_errors(response)
        return response.json()

    def search_by_keyword(self, keyword: str, **kwargs) -> dict:
        """通过关键词搜索（标题 + 摘要 + 关键词字段） / Search by keyword (title + abstract + keywords)"""
        query = f"TITLE-ABS-KEY({keyword})"
        return self.search(query, **kwargs)

    def search_by_author(self, author: str, **kwargs) -> dict:
        """通过作者名搜索 / Search by author name"""
        query = f"AUTH({author})"
        return self.search(query, **kwargs)

    def search_by_doi(self, doi: str, **kwargs) -> dict:
        """通过 DOI 搜索 / Search by DOI"""
        query = f'DOI("{doi}")'
        return self.search(query, **kwargs)

    def search_all_pages(
        self,
        query: str,
        max_results: int = 200,
        page_size: int = 25,
        **kwargs,
    ) -> list[dict]:
        """
        自动分页获取所有结果。
        Automatically handle pagination to fetch all results.

        Args:
            query: 搜索表达式 / Search expression
            max_results: 最大结果数 / Maximum number of results
            page_size: 每页结果数 / Results per page
            **kwargs: 传递给 search() 的其他参数 / Other parameters passed to search()

        Returns:
            所有结果条目的列表 / List of all result entries
        """
        all_entries = []
        start = 0
        page_size = min(page_size, 100)

        while start < max_results:
            count = min(page_size, max_results - start)
            data = self.search(query, count=count, start=start, **kwargs)

            results = data.get("search-results", {})
            entries = results.get("entry", [])

            # 如果没有更多结果或遇到错误条目，停止 / Stop if no more results or an error entry is encountered
            if not entries or (len(entries) == 1 and "error" in entries[0]):
                break

            all_entries.extend(entries)

            # 检查是否已获取所有结果 / Check if all results have been fetched
            total = int(results.get("opensearch:totalResults", 0))
            if start + len(entries) >= total:
                break

            start += len(entries)

        return all_entries[:max_results]

    @staticmethod
    def _handle_errors(response: requests.Response):
        """处理 HTTP 错误状态码 / Handle HTTP error status codes"""
        if response.status_code == 200:
            return

        status = response.status_code
        try:
            error_data = response.json()
            msg = str(error_data)
        except Exception:
            msg = response.text[:500]

        if status == 401:
            raise ScopusAuthError(f"认证失败 (401): API Key 无效或缺失 / Authentication failed: API Key missing or invalid。\n{msg}")
        elif status == 429:
            raise ScopusQuotaError(
                f"配额超限 (429): API 调用次数超过限制 / Quota exceeded: API calls over limit。\n{msg}\n"
                "请稍后再试，或在 https://dev.elsevier.com/api_key_settings.html 查看配额。 / Please try again later, or check quota."
            )
        elif status == 400:
            raise ScopusAPIError(f"请求无效 (400): 搜索语法可能有误 / Bad Request: Search syntax might be wrong。\n{msg}")
        else:
            raise ScopusAPIError(f"API 错误 / API Error ({status}): {msg}")
