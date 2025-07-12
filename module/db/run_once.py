import sys
import os

# src をパスに追加（project/src/module/db/ → project/src へ）
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from module.db.database import init_db

init_db()
