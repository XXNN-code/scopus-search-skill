# Scopus Literature Search Tool

[English](README.md) | [中文](README_zh.md)

A command-line literature search tool based on the Elsevier Scopus Search API, supporting multiple keyword queries, sorting, pagination, and data export (CSV, RIS formats).

## Requirements

- Python 3.x
- [uv](https://github.com/astral-sh/uv) (Recommended Python package and environment manager)
- Windows PowerShell

## Installation Guide

1. **Clone or download the code** and enter the project directory:
   ```powershell
   cd 文献搜索
   ```

2. **Create a virtual environment**:
   Create a virtual environment using `uv`:
   ```powershell
   uv venv
   ```

3. **Activate the virtual environment**:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

4. **Install dependencies**:
   ```powershell
   uv pip install -r scripts/requirements.txt
   ```

5. **Configure API Key**:
   - Copy `scripts/.env.example` to `scripts/.env` (if example file not present, just create `.env`).
   - Visit the [Elsevier Developer Portal](https://dev.elsevier.com/apikey/manage) to apply for an API Key.
   - Fill the obtained API Key into the `scripts/.env` file:
     ```env
     SCOPUS_API_KEY=your_actual_api_key_here
     ```

## Usage

All commands can be executed via `uv run scripts/main.py`.

### Common Command Examples

**1. Basic Keyword Search (Searches title, abstract, and keywords)**
```powershell
# Single keyword (defaults to TITLE-ABS-KEY search)
uv run scripts/main.py search "machine learning"

# Multiple keywords combined search (Note: when using AND/OR logic in PowerShell, wrap the entire phrase in single quotes)
uv run scripts/main.py search '"machine learning" AND PINN'
```

**2. Search by Author**
```powershell
uv run scripts/main.py search --author "Smith, J."
```

**3. Search by DOI**
```powershell
uv run scripts/main.py search --doi "10.1016/j.example.2024.01.001"
```

**4. Advanced Custom Search (Using Scopus Syntax)**
```powershell
uv run scripts/main.py search "TITLE-ABS-KEY(deep learning) AND PUBYEAR > 2020"
```

**5. Export to CSV or RIS file**
```powershell
# Export detailed results including abstracts to CSV
uv run scripts/main.py search --keyword "quantum computing" --view COMPLETE --format csv --output results.csv

# Export RIS format (can be imported into citation managers like EndNote, Zotero)
uv run scripts/main.py search "TITLE(neural network)" --format ris --output refs.ris
```

**6. Automatically fetch large number of papers with pagination, sorted by date descending**
```powershell
# Fetch the latest 150 papers, handling pagination automatically
uv run scripts/main.py search --keyword "large language model" --sort "-date" --max-results 150
```

### Full Parameter Reference

Run `uv run scripts/main.py search --help` to view complete help information.

**Search Options (Mutually exclusive, choose one)**:
- `query`: Search term or custom expression. If only text is provided, **defaults to TITLE-ABS-KEY search**.
- `--keyword`, `-k`: Search by keyword.
- `--author`, `-a`: Search by author.
- `--doi`, `-d`: Search by DOI.

**Pagination & Sorting**:
- `--count`, `-n`: Results per page (default 25, max 100).
- `--start`: Starting index (default 0).
- `--sort`, `-s`: Sort method, **default `-date` (descending by date)**. Can also specify e.g., `+citedby-count` (ascending by citations).
- `--view`, `-v`: View mode. Default `STANDARD`. Set to `COMPLETE` to get abstracts and keywords.
- `--max-results`, `-m`: Maximum results to fetch, program will auto-paginate (`default 50`, e.g., set to 200 to fetch more).

**Output Options**:
- `--format`, `-f`: Output format. **Default `auto`** (previews first 10 results in terminal, and exports full results as an RIS file). Options: `table` (pure terminal table), `detail` (pure terminal detailed text), `csv`, or `ris` (export file only without terminal preview).
- `--output`, `-o`: Export file path. If not specified in `auto` mode, it saves as `results.ris` in the current directory by default.

### Scopus Search Syntax Reference (Boolean Query)

* `TITLE-ABS-KEY(term)` — Search title, abstract, and keywords
* `AUTH(name)` — Search author
* `DOI(doi)` — Search DOI
* `TITLE(term)` — Search title only
* `ABS(term)` — Search abstract only
* `KEY(term)` — Search keyword only
* `AFFIL(name)` — Search affiliation
* `SRCTITLE(name)` — Search source title (journal name)
* `PUBYEAR > 2020` — Filter by year
* Logical combinations: `AND`, `OR`, `AND NOT`.

## Notes

- The Scopus API has rate limits. If using `--max-results` for large pulls, be mindful of your API Quota consumption.
- When querying in Windows PowerShell, if there are special characters or parentheses, it is recommended to wrap the query string in double quotes `""`.