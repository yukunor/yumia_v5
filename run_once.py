import sys
import os

# 「src」の一つ上のディレクトリをPythonパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from module.db.database import init_db

init_db()
