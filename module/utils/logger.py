# module/utils/logger.py の末尾に追記
if __name__ == "__main__":
    print("=== Logger Test Start ===", flush=True)
    logger.debug("🌟 デバッグ動作確認")
    logger.info("🔔 通常の情報ログ")
    print("=== Logger Test End ===", flush=True)
