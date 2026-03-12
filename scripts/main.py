"""Scopus 文献搜索 - 命令行入口 / Scopus Literature Search - CLI Entry Point"""

import argparse
import sys
import re
from datetime import datetime

from config import (
    SCOPUS_API_KEY, DEFAULT_COUNT, DEFAULT_VIEW, 
    DEFAULT_SORT, DEFAULT_MAX_RESULTS, DEFAULT_FORMAT
)
from scopus_client import ScopusClient, ScopusAPIError
from formatter import parse_entries, get_total_results, output_results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scopus-search",
        description="Scopus 文献搜索工具 — 基于 Elsevier Scopus Search API / Scopus Literature Search Tool - Based on Elsevier Scopus Search API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
搜索示例 / Search Examples:
  %(prog)s search "TITLE-ABS-KEY(deep learning)"
  %(prog)s search --keyword "machine learning"
  %(prog)s search --author "Smith, J."
  %(prog)s search --doi "10.1016/j.example.2024.01.001"
  %(prog)s search --keyword "neural network" --sort "-date" --count 10
  %(prog)s search --keyword "quantum computing" --format json --output refs.json

搜索语法 (Boolean 查询) / Search Syntax (Boolean Query):
  TITLE-ABS-KEY(term)  — 搜索标题、摘要和关键词 / Search title, abstract & keywords
  AUTH(name)           — 搜索作者 / Search author
  DOI(doi)             — 搜索 DOI / Search DOI
  TITLE(term)          — 仅搜索标题 / Search title only
  ABS(term)            — 仅搜索摘要 / Search abstract only
  KEY(term)            — 仅搜索关键词 / Search keywords only
  AFFIL(name)          — 搜索机构 / Search affiliation
  SRCTITLE(name)       — 搜索期刊名 / Search journal (source title)
  PUBYEAR > 2020       — 按年份过滤 / Filter by year
  可使用 AND, OR, AND NOT 组合多个条件 / Use AND, OR, AND NOT to combine conditions
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令 / Available commands")

    # search 子命令 / search subcommand
    search_parser = subparsers.add_parser("search", help="搜索文献 / Search literature")

    # 搜索方式（互斥但可选） / Search options (mutually exclusive but optional)
    search_group = search_parser.add_argument_group("搜索方式 / Search Methods")
    search_group.add_argument(
        "query", nargs="?", default=None,
        help='搜索词 (默认按 TITLE-ABS-KEY 搜索), 或自定义搜索表达式: 如 "TITLE-ABS-KEY(deep learning)" / Search term (defaults to TITLE-ABS-KEY), or custom expression',
    )
    search_group.add_argument(
        "--keyword", "-k", default=None,
        help="按关键词搜索 (搜索标题+摘要+关键词字段) / Search by keyword",
    )
    search_group.add_argument(
        "--author", "-a", default=None,
        help='按作者搜索, 如 "Smith, J." / Search by author',
    )
    search_group.add_argument(
        "--doi", "-d", default=None,
        help="按 DOI 搜索 / Search by DOI",
    )

    # 搜索选项 / Search parameters
    option_group = search_parser.add_argument_group("搜索选项 / Search Parameters")
    option_group.add_argument(
        "--count", "-n", type=int, default=DEFAULT_COUNT,
        help=f"每页结果数 (默认 {DEFAULT_COUNT}, 最多 100) / Results per page (default {DEFAULT_COUNT}, max 100)",
    )
    option_group.add_argument(
        "--start", type=int, default=0,
        help="起始索引 (默认 0) / Starting index (default 0)",
    )
    option_group.add_argument(
        "--sort", "-s", default=DEFAULT_SORT,
        help=f'排序方式 / Sort method, 如 "-date" (降序), "+citedby-count" (升序) (默认 / Default {DEFAULT_SORT})',
    )
    option_group.add_argument(
        "--view", "-v", default=DEFAULT_VIEW,
        choices=["STANDARD", "COMPLETE"],
        help=f"视图模式 (默认 {DEFAULT_VIEW}; COMPLETE 包含摘要和关键词) / View mode (default {DEFAULT_VIEW}; COMPLETE includes abstract)",
    )
    option_group.add_argument(
        "--max-results", "-m", type=int, default=DEFAULT_MAX_RESULTS,
        help=f"最大结果数，自动分页获取 (默认 {DEFAULT_MAX_RESULTS}) / Max results to fetch with auto-pagination (default {DEFAULT_MAX_RESULTS})",
    )

    # 输出选项 / Output options
    output_group = search_parser.add_argument_group("输出选项 / Output Options")
    output_group.add_argument(
        "--format", "-f", dest="output_format", default=DEFAULT_FORMAT,
        choices=["auto", "table", "detail", "csv", "ris", "json"],
        help=f"输出格式 (默认 {DEFAULT_FORMAT}: 终端预览前10条并输出 JSON 文件) / Output format (default {DEFAULT_FORMAT}: preview table + JSON file)",
    )
    output_group.add_argument(
        "--output", "-o", default=None,
        help="导出到文件 (默认会使用 搜索词_日期.json) / Export to file",
    )

    return parser


def run_search(args):
    """执行搜索逻辑 / Execute search logic"""
    # 构建搜索查询 / Build search query
    client = ScopusClient(SCOPUS_API_KEY)

    search_kwargs = {
        "count": args.count,
        "start": args.start,
        "sort": args.sort,
        "view": args.view,
    }

    # 确定搜索方式 / Determine search method
    file_keyword_raw = "results"
    if args.keyword:
        query = f"TITLE-ABS-KEY({args.keyword})"
        file_keyword_raw = args.keyword
    elif args.author:
        query = f"AUTH({args.author})"
        file_keyword_raw = args.author
    elif args.doi:
        query = f'DOI("{args.doi}")'
        file_keyword_raw = args.doi.replace("/", "_")
    elif args.query:
        if "(" in args.query and ")" in args.query:
            query = args.query
        else:
            query = f"TITLE-ABS-KEY({args.query})"
        file_keyword_raw = args.query
    else:
        print("错误 / Error: 请提供搜索查询。使用 --help 查看用法。 / Please provide a search query. Use --help for usage.", file=sys.stderr)
        sys.exit(1)

    # 生成默认文件名 / Generate default file name
    safe_keyword = re.sub(r'[^\w\u4e00-\u9fa5]+', '_', file_keyword_raw).strip('_')
    if len(safe_keyword) > 50:
        safe_keyword = safe_keyword[:50].strip('_')
    if not safe_keyword:
        safe_keyword = "results"
    
    today_str = datetime.now().strftime("%Y%m%d")
    default_out_file = f"{safe_keyword}_{today_str}.json"

    print(f"正在搜索 / Searching: {query}")
    print(f"视图模式 / View mode: {args.view} | 排序 / Sort: {args.sort or '默认/Default'}")
    print()

    if args.max_results:
        # 自动分页获取 / Fetch with auto-pagination
        entries_raw = client.search_all_pages(
            query,
            max_results=args.max_results,
            page_size=args.count,
            sort=args.sort,
            view=args.view,
        )
        # 直接使用 raw entries 构建简化结构 / Build standard structure from raw entries
        # 因为 search_all_pages 返回的是原始条目列表, 需要包装成标准格式 / Because search_all_pages returns raw entries, wrap in standard format
        fake_response = {
            "search-results": {
                "opensearch:totalResults": str(len(entries_raw)),
                "entry": entries_raw,
            }
        }
        entries = parse_entries(fake_response)
        total = len(entries)
        print(f"共获取 {total} 条结果 (最大请求数: {args.max_results}) / Total fetched {total} results (Max cap: {args.max_results})")
    else:
        data = client.search(query, **search_kwargs)
        total = get_total_results(data)
        entries = parse_entries(data)
        showing = len(entries)
        print(f"共找到 {total} 条结果, 当前显示第 {args.start + 1}-{args.start + showing} 条 / Found {total} results, showing {args.start + 1}-{args.start + showing}")

    print()

    # 输出结果 / Output results
    if args.output_format == "auto":
        print("【预览前 10 条结果 / Preview of top 10 results】")
        output_results(entries[:10], fmt="table")
        
        out_file = args.output or default_out_file
        print(f"\n【自动导出 / Auto-export】正在将全部 {len(entries)} 条结果保存至 / Saving all {len(entries)} results to {out_file} ...")
        output_results(entries, fmt="json", output_file=out_file)
    else:
        output_results(entries, fmt=args.output_format, output_file=args.output)


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    try:
        if args.command == "search":
            run_search(args)
    except ScopusAPIError as e:
        print(f"\n✗ 错误 / Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n已取消。 / Cancelled.")
        sys.exit(0)


if __name__ == "__main__":
    main()
