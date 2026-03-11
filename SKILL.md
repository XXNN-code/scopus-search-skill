---
name: scopus-search
description: 使用 Scopus API 搜索学术文献、期刊、作者或 DOI。当用户需要查找学术论文、在 Scopus 上进行文献检索，或需要导出文献的 CSV/RIS 格式时，请立刻并始终触发此技能。支持包含复杂布尔查询、分页和自动导出的命令行工具。
---

# Scopus Literature Search (Scopus 文献搜索技能)

通过此技能，你可以代表用户使用基于 Elsevier Scopus API 的内置 Python 命令行工具进行文献和学术资料搜索。所有资源已打包在 `scripts/` 目录中。

## 运行环境准备

在开始 any 搜索之前，确认你的工作路径下有正确的依赖：
1. 始终优先在包含本工具的目录下运行命令（或者在终端以该目录为当前目录）。
2. 在此工具第一次使用时，确保用户有包含 `SCOPUS_API_KEY=xxx` 的 `scripts/.env`。没有时请向用户询问或者提醒他们创建。
3. 提示：该工具默认运行环境为已包含必要依赖的 `uv venv` 环境下，可以通过 `uv run scripts/main.py` 直接执行。

## 使用方法 (Usage)

注意：所有的命令必须使用 `uv run scripts/main.py` 作为前缀在 PowerShell 中执行。

### 1. 基础搜索

- 单个或常规组合词 (搜索标题、摘要和关键词)：
  ```powershell
  uv run scripts/main.py search "machine learning"
  uv run scripts/main.py search '"machine learning" AND PINN'
  ```
- 按照作者搜索：
  ```powershell
  uv run scripts/main.py search --author "Smith, J."
  ```
- 按照 DOI 搜索：
  ```powershell
  uv run scripts/main.py search --doi "10.1016/j.example.2024.01.001"
  ```

### 2. 高级逻辑组合搜索

Scopus 支持高级布尔查询语法。
- 支持检索字段：`TITLE-ABS-KEY(term)`、`AUTH(name)`、`DOI(doi)`、`TITLE(term)`、`ABS(term)`、`KEY(term)`、`PUBYEAR > 2020` 等。
- 支持逻辑符：`AND`, `OR`, `AND NOT`

**用例**：
```powershell
uv run scripts/main.py search "TITLE-ABS-KEY(deep learning) AND PUBYEAR > 2020"
```
*(注意包裹整个短语的双引号)*

### 3. 数据导出和大规模获取

该工具具有优秀的数据格式导出（支持 RIS 以及 CSV）以及自动翻页能力（能绕过单页获取不超过 100 篇文献的限制）：
- 终端详细结果表格导出为可以导入 EndNote/Zotero 的 RIS 格式：
  ```powershell
  uv run scripts/main.py search "TITLE(neural network)" --format ris --output refs.ris
  ```
- 将摘要（COMPLETE view）一并保存为 CSV：
  ```powershell
  uv run scripts/main.py search --keyword "quantum computing" --view COMPLETE --format csv --output results.csv
  ```
- 获取最新的 150 篇关于大语言模型的文献（触发自动翻页拉取，按时间降序）：
  ```powershell
  uv run scripts/main.py search --keyword "large language model" --sort "-date" --max-results 150
  ```

### 参数提醒与默认值
- `query`：无前缀则默认为 `TITLE-ABS-KEY` 全文匹配。
- `--sort`, `-s`：默认为 `-date`（按日期降序），也可设置为升降序如 `+citedby-count`（按被引用量升序排）。
- `--view`, `-v`：默认 `STANDARD`。需拉取摘要，加上 `--view COMPLETE`。

## Agent 工作流建议

如果用户请求进行文献搜索：
1. 分析他们提供的关键词/要求，构造一条合适的 `main.py search` 指令。
2. 运行检索，检查终端的前 10 名输出摘要和数量。
3. 帮助他们读取、解读搜索的结果或者总结导出的文件中的论文概述。
