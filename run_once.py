import sys
import os

# module/ をPythonパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), "module"))

from db.database import init_db

init_db()
