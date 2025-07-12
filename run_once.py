import sys
import os

# 現在のディレクトリのパス（project/src）をPythonパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.database import init_db

init_db()
