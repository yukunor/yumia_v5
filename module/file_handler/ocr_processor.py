# module/file_handler/image_processor.py

import os
from PIL import Image

def process_image(file_path: str) -> str:
    """
    画像ファイルを処理し、次の処理用に内容またはファイルパスを返す。
    （現時点では画像のそのままのパスを返すのみ。将来的に分類やキャプション生成を追加予定）
    
    Args:
        file_path (str): 保存された画像ファイルのパス

    Returns:
        str: 処理された画像のファイルパス
    """
    try:
        # 画像として読み込み確認（必要ならここでリサイズ・正規化なども可）
        img = Image.open(file_path)
        img.verify()  # 画像ファイルの整合性確認
        return file_path
    except Exception as e:
        print(f"[ERROR] 画像処理失敗: {e}")
        return ""

# 今後、ここに画像分類器やキャプション生成などの拡張処理を追加していく予定
