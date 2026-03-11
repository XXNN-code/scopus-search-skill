"""结果格式化模块 - 支持表格、详细、CSV、RIS 输出"""

import csv
import io
import sys


# Scopus 文献类型 -> RIS 文献类型映射
_DOCTYPE_TO_RIS = {
    "ar": "JOUR",   # Article -> Journal Article
    "re": "JOUR",   # Review -> Journal Article
    "cp": "CONF",   # Conference Paper
    "ch": "CHAP",   # Book Chapter
    "bk": "BOOK",   # Book
    "le": "JOUR",   # Letter
    "no": "JOUR",   # Note
    "ed": "JOUR",   # Editorial
    "sh": "JOUR",   # Short Survey
    "er": "JOUR",   # Erratum
}


def parse_entries(data: dict) -> list[dict]:
    """
    从 API 响应中解析文献条目列表。

    Args:
        data: API 返回的 JSON 字典

    Returns:
        文献条目列表，每个条目是一个简化后的字典
    """
    results = data.get("search-results", {})
    raw_entries = results.get("entry", [])
    total = results.get("opensearch:totalResults", "0")

    entries = []
    for raw in raw_entries:
        # 跳过错误条目
        if "error" in raw:
            continue

        # 提取 Scopus 链接
        scopus_link = ""
        for link in raw.get("link", []):
            if link.get("@ref") == "scopus":
                scopus_link = link.get("@href", "")
                break

        # 解析页码范围
        page_range = raw.get("prism:pageRange", "")
        start_page, end_page = "", ""
        if page_range and "-" in page_range:
            parts = page_range.split("-", 1)
            start_page, end_page = parts[0].strip(), parts[1].strip()
        elif page_range:
            start_page = page_range

        # 提取所有作者（COMPLETE 视图下）
        authors = []
        for author in raw.get("author", []):
            name = author.get("authname", "")
            if name:
                authors.append(name)

        # 提取关键词
        keywords_str = raw.get("authkeywords", "")
        keywords = []
        if keywords_str:
            keywords = [k.strip() for k in keywords_str.split("|")]

        entry = {
            "title": raw.get("dc:title", "N/A"),
            "first_author": raw.get("dc:creator", "N/A"),
            "authors": authors if authors else [raw.get("dc:creator", "N/A")],
            "journal": raw.get("prism:publicationName", "N/A"),
            "volume": raw.get("prism:volume", ""),
            "issue": raw.get("prism:issueIdentifier", ""),
            "pages": page_range,
            "start_page": start_page,
            "end_page": end_page,
            "date": raw.get("prism:coverDate", "N/A"),
            "year": raw.get("prism:coverDate", "")[:4],
            "doi": raw.get("prism:doi", ""),
            "cited_by": raw.get("citedby-count", "0"),
            "abstract": raw.get("dc:description", ""),
            "scopus_id": raw.get("dc:identifier", ""),
            "scopus_link": scopus_link,
            "doc_type": raw.get("subtype", ""),
            "doc_type_desc": raw.get("subtypeDescription", ""),
            "issn": raw.get("prism:issn", ""),
            "eissn": raw.get("prism:eIssn", ""),
            "keywords": keywords,
            "open_access": raw.get("openaccess", ""),
        }
        entries.append(entry)

    return entries


def get_total_results(data: dict) -> int:
    """获取搜索结果总数"""
    return int(data.get("search-results", {}).get("opensearch:totalResults", 0))


def format_table(entries: list[dict]) -> str:
    """格式化为简洁表格"""
    if not entries:
        return "未找到任何结果。"

    lines = []
    # 表头
    lines.append(f"{'序号':>4}  {'标题':<50}  {'第一作者':<20}  {'期刊':<30}  {'年份':>6}  {'引用':>6}  {'DOI'}")
    lines.append("─" * 160)

    for i, e in enumerate(entries, 1):
        title = e["title"][:48] + "…" if len(e["title"]) > 50 else e["title"]
        author = e["first_author"][:18] + "…" if len(e["first_author"]) > 20 else e["first_author"]
        journal = e["journal"][:28] + "…" if len(e["journal"]) > 30 else e["journal"]
        lines.append(
            f"{i:>4}  {title:<50}  {author:<20}  {journal:<30}  {e['year']:>6}  {e['cited_by']:>6}  {e['doi']}"
        )

    return "\n".join(lines)


def format_detail(entries: list[dict]) -> str:
    """格式化为详细信息"""
    if not entries:
        return "未找到任何结果。"

    blocks = []
    for i, e in enumerate(entries, 1):
        block = [
            f"═══ [{i}] ═══════════════════════════════════════════",
            f"  标题: {e['title']}",
            f"  作者: {', '.join(e['authors'])}",
            f"  期刊: {e['journal']}",
        ]
        if e["volume"] or e["issue"]:
            vol_issue = f"  卷/期: {e['volume']}"
            if e["issue"]:
                vol_issue += f"({e['issue']})"
            block.append(vol_issue)
        if e["pages"]:
            block.append(f"  页码: {e['pages']}")
        block.append(f"  日期: {e['date']}")
        if e["doi"]:
            block.append(f"  DOI: {e['doi']}")
        block.append(f"  引用数: {e['cited_by']}")
        if e["doc_type_desc"]:
            block.append(f"  文献类型: {e['doc_type_desc']}")
        if e["open_access"]:
            oa_text = "是" if e["open_access"] == "1" else "否"
            block.append(f"  开放获取: {oa_text}")
        if e["keywords"]:
            block.append(f"  关键词: {'; '.join(e['keywords'])}")
        if e["abstract"]:
            abstract = e["abstract"][:300]
            if len(e["abstract"]) > 300:
                abstract += "…"
            block.append(f"  摘要: {abstract}")
        if e["scopus_link"]:
            block.append(f"  链接: {e['scopus_link']}")

        blocks.append("\n".join(block))

    return "\n\n".join(blocks)


def format_csv(entries: list[dict]) -> str:
    """格式化为 CSV"""
    if not entries:
        return ""

    output = io.StringIO()
    writer = csv.writer(output)

    # 表头
    writer.writerow([
        "序号", "标题", "作者", "期刊", "卷", "期", "页码",
        "日期", "DOI", "引用数", "文献类型", "关键词", "摘要", "链接",
    ])

    for i, e in enumerate(entries, 1):
        writer.writerow([
            i,
            e["title"],
            "; ".join(e["authors"]),
            e["journal"],
            e["volume"],
            e["issue"],
            e["pages"],
            e["date"],
            e["doi"],
            e["cited_by"],
            e["doc_type_desc"],
            "; ".join(e["keywords"]),
            e["abstract"],
            e["scopus_link"],
        ])

    return output.getvalue()


def format_ris(entries: list[dict]) -> str:
    """
    格式化为 RIS 格式。

    RIS 格式兼容 EndNote、Zotero、Mendeley 等文献管理软件。
    参考: https://en.wikipedia.org/wiki/RIS_(file_format)
    """
    if not entries:
        return ""

    lines = []
    for e in entries:
        # 文献类型
        ris_type = _DOCTYPE_TO_RIS.get(e["doc_type"], "GEN")
        lines.append(f"TY  - {ris_type}")

        # 标题
        lines.append(f"TI  - {e['title']}")

        # 作者（每个作者一行）
        for author in e["authors"]:
            lines.append(f"AU  - {author}")

        # 期刊
        if e["journal"] and e["journal"] != "N/A":
            lines.append(f"JO  - {e['journal']}")

        # 卷
        if e["volume"]:
            lines.append(f"VL  - {e['volume']}")

        # 期
        if e["issue"]:
            lines.append(f"IS  - {e['issue']}")

        # 页码
        if e["start_page"]:
            lines.append(f"SP  - {e['start_page']}")
        if e["end_page"]:
            lines.append(f"EP  - {e['end_page']}")

        # 年份
        if e["year"]:
            lines.append(f"PY  - {e['year']}")

        # 日期
        if e["date"] and e["date"] != "N/A":
            lines.append(f"DA  - {e['date'].replace('-', '/')}")

        # DOI
        if e["doi"]:
            lines.append(f"DO  - {e['doi']}")

        # 摘要
        if e["abstract"]:
            lines.append(f"AB  - {e['abstract']}")

        # 关键词（每个关键词一行）
        for kw in e["keywords"]:
            lines.append(f"KW  - {kw}")

        # ISSN
        if e["issn"]:
            lines.append(f"SN  - {e['issn']}")

        # 链接
        if e["scopus_link"]:
            lines.append(f"UR  - {e['scopus_link']}")

        # Scopus ID
        if e["scopus_id"]:
            lines.append(f"AN  - {e['scopus_id']}")

        # 条目结束标记
        lines.append("ER  - ")
        lines.append("")  # 空行分隔

    return "\n".join(lines)


def output_results(
    entries: list[dict],
    fmt: str = "table",
    output_file: str | None = None,
):
    """
    按指定格式输出结果。

    Args:
        entries: 文献条目列表
        fmt: 输出格式 (table/detail/csv/ris)
        output_file: 输出文件路径（为 None 则输出到终端）
    """
    formatters = {
        "table": format_table,
        "detail": format_detail,
        "csv": format_csv,
        "ris": format_ris,
    }

    formatter = formatters.get(fmt)
    if not formatter:
        print(f"不支持的输出格式: {fmt}，可选: {', '.join(formatters.keys())}")
        return

    content = formatter(entries)

    if output_file:
        encoding = "utf-8"
        with open(output_file, "w", encoding=encoding, newline="") as f:
            f.write(content)
        print(f"结果已导出到: {output_file}")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(content)
