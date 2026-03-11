"""配置管理模块 - 加载 API Key 和默认参数"""

import os
from dotenv import load_dotenv

# 加载 .env 文件（尝试从当前目录和脚本所在目录加载）
base_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv()  # 先从项目根目录（运行目录）加载
load_dotenv(os.path.join(base_dir, ".env"))  # 再尝试从脚本目录加载

# Scopus API 配置
SCOPUS_API_KEY = os.getenv("SCOPUS_API_KEY", "").strip()
SCOPUS_SEARCH_URL = "https://api.elsevier.com/content/search/scopus"

# 默认参数
DEFAULT_COUNT = 25       # 每页结果数（最多 100）
DEFAULT_VIEW = "STANDARD"  # 视图模式: STANDARD 或 COMPLETE
DEFAULT_SORT = "-date"     # 排序方式: 如 -date (按日期降序)
DEFAULT_MAX_RESULTS = 50   # 默认最大获取结果数
DEFAULT_FORMAT = "auto"    # 默认输出格式
