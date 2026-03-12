---
name: scopus-search
description: Search academic literature, journals, authors, or DOIs using the Scopus API. Always trigger this skill when the user needs to find academic papers, conduct literature searches on Scopus, or export literature references in JSON/CSV/RIS format. Supports complex boolean queries, pagination, and automated data export via a CLI tool.
---

# Scopus Literature Search Skill

[English](SKILL.md) | [中文](SKILL_zh.md)

Through this skill, you can use the built-in Python command-line tool based on the Elsevier Scopus API to perform literature and academic resource searches on behalf of the user. All resources are bundled in the `scripts/` directory.

## Runtime Environment Preparation

Before starting any searches, ensure you have the correct dependencies in your working directory:
1. Always prioritize running commands in the directory containing this tool (or set the terminal's current directory to it).
2. Upon first use, ensure the user has a `scripts/.env` file containing `SCOPUS_API_KEY=xxx`. If missing, ask the user or remind them to create it.
3. Tip: The default runtime environment for this tool is under the `uv venv` which already contains necessary dependencies. You can execute commands directly via `uv run scripts/main.py`.

## Usage

Note: All commands MUST be prefixed with `uv run scripts/main.py` and executed in PowerShell.

### 1. Basic Search

- Single or regular combined terms (Searches title, abstract, and keywords):
  ```powershell
  uv run scripts/main.py search "machine learning"
  uv run scripts/main.py search '"machine learning" AND PINN'
  ```
- Search by author:
  ```powershell
  uv run scripts/main.py search --author "Smith, J."
  ```
- Search by DOI:
  ```powershell
  uv run scripts/main.py search --doi "10.1016/j.example.2024.01.001"
  ```

### 2. Advanced Logical Search

Scopus supports advanced boolean query syntax.
- Supported search fields: `TITLE-ABS-KEY(term)`, `AUTH(name)`, `DOI(doi)`, `TITLE(term)`, `ABS(term)`, `KEY(term)`, `PUBYEAR > 2020`, etc.
- Logical operators: `AND`, `OR`, `AND NOT`

**Use Case**:
```powershell
uv run scripts/main.py search "TITLE-ABS-KEY(deep learning) AND PUBYEAR > 2020"
```
*(Note the double quotes wrapping the entire phrase)*

### 3. Data Export and Large-Scale Retrieval

This tool features excellent data format export (supporting JSON, RIS and CSV) and automatic pagination handling (bypassing the single-page limit of 100 papers):
- Export terminal detailed results table to RIS format, which can be imported into EndNote/Zotero:
  ```powershell
  uv run scripts/main.py search "TITLE(neural network)" --format ris --output refs.ris
  ```
- Save abstracts (`COMPLETE` view) to CSV:
  ```powershell
  uv run scripts/main.py search --keyword "quantum computing" --view COMPLETE --format csv --output results.csv
  ```
- Fetch the latest 150 papers on large language models (triggers auto-pagination, descending by date):
  ```powershell
  uv run scripts/main.py search --keyword "large language model" --sort "-date" --max-results 150
  ```

### Parameter Reminders and Defaults
- `query`: No prefix defaults to `TITLE-ABS-KEY` full-text match.
- `--sort`, `-s`: Defaults to `-date` (descending by date). Can also be ascending, e.g., `+citedby-count` (ascending by citation count).
- `--view`, `-v`: Defaults to `STANDARD`. To fetch abstracts, add `--view COMPLETE`.
- `--output`, `-o`: If not provided in `auto` mode, the tool automatically generates a filename like `keyword_YYYYMMDD.json`.

## Agent Workflow Suggestions

If the user requests a literature search:
1. Analyze the keywords/requirements they provide and construct an appropriate `main.py search` command.
2. Run the search, and examine the top 10 output abstracts and total count in the terminal.
3. Help them read and interpret the search results, or summarize the paper overviews in the exported files.
