"""配置管理模块 - 加载 API Key 和默认参数 / Configuration module - Load API Key and default parameters"""

import os
from dotenv import load_dotenv

# 加载 .env 文件（尝试从当前目录和脚本所在目录加载）
# Load .env file (try loading from current working directory and script directory)
base_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv()  # 先从项目根目录（运行目录）加载 / Load from project root (runtime directory) first
load_dotenv(os.path.join(base_dir, ".env"))  # 再尝试从脚本目录加载 / Then try loading from script directory

# Scopus API 配置 / Scopus API Configuration
SCOPUS_API_KEY = os.getenv("SCOPUS_API_KEY", "").strip()
SCOPUS_SEARCH_URL = "https://api.elsevier.com/content/search/scopus"

# 默认参数 / Default parameters
DEFAULT_COUNT = 25       # 每页结果数（最多 100） / Results per page (max 100)
DEFAULT_VIEW = "STANDARD"  # 视图模式: STANDARD 或 COMPLETE / View mode: STANDARD or COMPLETE
DEFAULT_SORT = "-date"     # 排序方式: 如 -date (按日期降序) / Sort method: e.g., -date (descending by date)
DEFAULT_MAX_RESULTS = 50   # 默认最大获取结果数 / Default maximum results to fetch
DEFAULT_FORMAT = "auto"    # 默认输出格式 / Default output format
