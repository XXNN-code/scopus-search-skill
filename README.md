# Scopus 文献搜索工具

基于 Elsevier Scopus Search API 的命令行文献搜索工具，支持多种关键词查询、排序、分页以及数据导出（CSV、RIS 等格式）。

## 环境要求

- Python 3.x
- [uv](https://github.com/astral-sh/uv) (推荐的 Python 包 and 环境管理器)
- Windows PowerShell

## 安装指南

1. **克隆或下载代码**进入项目目录：
   ```powershell
   cd 文献搜索
   ```

2. **创建虚拟环境**：
   使用 `uv` 创建虚拟环境：
   ```powershell
   uv venv
   ```

3. **激活虚拟环境**：
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

4. **安装依赖**：
   ```powershell
   uv pip install -r scripts/requirements.txt
   ```

5. **配置 API Key**：
   - 复制 `scripts/.env.example` 文件并重命名为 `scripts/.env`。
   - 访问 [Elsevier Developer Portal](https://dev.elsevier.com/apikey/manage) 申请 API Key。
   - 将获取到的 API Key 填入 `scripts/.env` 文件中：
     ```env
     SCOPUS_API_KEY=换成你的真实API_KEY
     ```

## 使用方法

所有的命令都可以通过 `uv run scripts/main.py` 来执行。

### 常用命令示例

**1. 基础关键词搜索（搜索标题、摘要和关键词）**
```powershell
# 单个关键词 (现在默认会按 TITLE-ABS-KEY 搜索)
uv run scripts/main.py search "machine learning"

# 多个关键词组合搜索 (注意：在 PowerShell 中包含 AND/OR 逻辑时，需要将整个词组用单引号包裹)
uv run scripts/main.py search '"machine learning" AND PINN'
```

**2. 按作者搜索**
```powershell
uv run scripts/main.py search --author "Smith, J."
```

**3. 按 DOI 搜索**
```powershell
uv run scripts/main.py search --doi "10.1016/j.example.2024.01.001"
```

**4. 高级自定义搜索（使用 Scopus 语法）**
```powershell
uv run scripts/main.py search "TITLE-ABS-KEY(deep learning) AND PUBYEAR > 2020"
```

**5. 导出为 CSV 或 RIS 文件**
```powershell
# 导出包含摘要的详细结果到 CSV
uv run scripts/main.py search --keyword "quantum computing" --view COMPLETE --format csv --output results.csv

# 导出 RIS 格式（可导入 EndNote, Zotero 等文献管理软件）
uv run scripts/main.py search "TITLE(neural network)" --format ris --output refs.ris
```

**6. 自动分页获取大量文献并按日期降序排列**
```powershell
# 获取最新的 150 篇文献，自动处理分页
uv run scripts/main.py search --keyword "large language model" --sort "-date" --max-results 150
```

### 完整参数说明

运行 `uv run scripts/main.py search --help` 可以查看完整的帮助信息。

**搜索方式（互斥，任选其一即可）**：
- `query`: 搜索词或自定义表达式。若只输入文本，**默认按 TITLE-ABS-KEY 搜索**。
- `--keyword`, `-k`: 按关键词搜索。
- `--author`, `-a`: 按作者搜索。
- `--doi`, `-d`: 按 DOI 搜索。

**搜索选项**：
- `--count`, `-n`: 每页结果数（默认 25，最大 100）。
- `--start`: 起始索引（默认 0）。
- `--sort`, `-s`: 排序方式，**默认 `-date`（按日期降序）**，也可指定如 `+citedby-count`（被引次数升序）。
- `--view`, `-v`: 视图模式。默认 `STANDARD`。如需获取摘要和关键字，请设置为 `COMPLETE`。
- `--max-results`, `-m`: 最大获取结果数，程序会自动分页拉取数据（**默认 50**，例如设置 `--max-results 200` 拉取更多）。

**输出选项**：
- `--format`, `-f`: 输出格式。**默认 `auto`**（在终端预览前 10 条结果的表格，同时将完整结果导出为 RIS 文件）。也可选择 `table`（纯终端表格）、`detail`（纯终端详细）、`csv` 或 `ris`（仅导出文件而不预览）。
- `--output`, `-o`: 导出文件的路径。若在 `auto` 模式下不指定，默认会保存为当前目录的 `results.ris`。

### Scopus 搜索语法参考 (Boolean 查询)

* `TITLE-ABS-KEY(term)` — 搜索标题、摘要和关键词
* `AUTH(name)` — 搜索作者
* `DOI(doi)` — 搜索 DOI
* `TITLE(term)` — 仅搜索标题
* `ABS(term)` — 仅搜索摘要
* `KEY(term)` — 仅搜索关键词
* `AFFIL(name)` — 搜索机构
* `SRCTITLE(name)` — 搜索期刊 (Source Title)
* `PUBYEAR > 2020` — 按年份过滤条件
* 逻辑组合：可使用 `AND`, `OR`, `AND NOT` 组合多个条件。

## 注意事项

- Scopus API 有一定的调用频率限制，如果配合 `--max-results` 进行大量拉取，请注意 API Quota 的配额消耗。
- 若要在 Windows PowerShell 下进行查询，当存在特殊字符或括号时，建议给查询字符串加上双引号 `""`。
