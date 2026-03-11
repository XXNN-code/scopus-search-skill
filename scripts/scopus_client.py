"""Scopus API 客户端 - 封装搜索请求和分页逻辑"""

import requests
from config import SCOPUS_SEARCH_URL, DEFAULT_COUNT, DEFAULT_VIEW


class ScopusAPIError(Exception):
    """Scopus API 错误基类"""
    pass


class ScopusAuthError(ScopusAPIError):
    """认证错误 (401)"""
    pass


class ScopusQuotaError(ScopusAPIError):
    """配额超限错误 (429)"""
    pass


class ScopusClient:
    """Scopus Search API 客户端"""

    def __init__(self, api_key: str):
        if not api_key:
            raise ScopusAuthError(
                "未提供 API Key。请在 .env 文件中设置 SCOPUS_API_KEY，\n"
                "或在 https://dev.elsevier.com/apikey/manage 注册获取。"
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

        Args:
            query: Boolean 搜索表达式, 如 "TITLE-ABS-KEY(deep learning)"
            count: 每页结果数 (1-100)
            start: 起始索引
            sort: 排序方式, 如 "-date", "+citedby-count"
            view: 视图模式 "STANDARD" 或 "COMPLETE"
            field: 返回的指定字段, 逗号分隔

        Returns:
            解析后的 JSON 响应字典

        Raises:
            ScopusAuthError: API Key 无效或缺失
            ScopusQuotaError: API 调用配额超限
            ScopusAPIError: 其他 API 错误
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
        """通过关键词搜索（标题 + 摘要 + 关键词字段）"""
        query = f"TITLE-ABS-KEY({keyword})"
        return self.search(query, **kwargs)

    def search_by_author(self, author: str, **kwargs) -> dict:
        """通过作者名搜索"""
        query = f"AUTH({author})"
        return self.search(query, **kwargs)

    def search_by_doi(self, doi: str, **kwargs) -> dict:
        """通过 DOI 搜索"""
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

        Args:
            query: 搜索表达式
            max_results: 最大结果数
            page_size: 每页结果数
            **kwargs: 传递给 search() 的其他参数

        Returns:
            所有结果条目的列表
        """
        all_entries = []
        start = 0
        page_size = min(page_size, 100)

        while start < max_results:
            count = min(page_size, max_results - start)
            data = self.search(query, count=count, start=start, **kwargs)

            results = data.get("search-results", {})
            entries = results.get("entry", [])

            # 如果没有更多结果或遇到错误条目，停止
            if not entries or (len(entries) == 1 and "error" in entries[0]):
                break

            all_entries.extend(entries)

            # 检查是否已获取所有结果
            total = int(results.get("opensearch:totalResults", 0))
            if start + len(entries) >= total:
                break

            start += len(entries)

        return all_entries[:max_results]

    @staticmethod
    def _handle_errors(response: requests.Response):
        """处理 HTTP 错误状态码"""
        if response.status_code == 200:
            return

        status = response.status_code
        try:
            error_data = response.json()
            msg = str(error_data)
        except Exception:
            msg = response.text[:500]

        if status == 401:
            raise ScopusAuthError(f"认证失败 (401): API Key 无效或缺失。\n{msg}")
        elif status == 429:
            raise ScopusQuotaError(
                f"配额超限 (429): API 调用次数超过限制。\n{msg}\n"
                "请稍后再试，或在 https://dev.elsevier.com/api_key_settings.html 查看配额。"
            )
        elif status == 400:
            raise ScopusAPIError(f"请求无效 (400): 搜索语法可能有误。\n{msg}")
        else:
            raise ScopusAPIError(f"API 错误 ({status}): {msg}")
