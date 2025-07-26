# module/oblivion/oblivion_module.py

from module.oblivion.oblivion_intermediate import get_expired_intermediate_emotions, save_oblivion_intermediate_entries
from module.oblivion.oblivion_short import get_expired_short_term_emotions, save_oblivion_short_entries
from module.oblivion.oblivion_purge import delete_expired_oblivion_entries, delete_expired_short_oblivion_entries
from module.oblivion.oblivion_index import remove_index_entries_by_date, remove_history_entries_by_date


from module.utils.utils import logger

#intermediateカテゴリに関する忘却処理をまとめて呼び出す。
def run_intermediate_oblivion_process():
    logger.info("📦 [START] intermediate忘却プロセスの実行")
    expired = get_expired_intermediate_emotions()
    logger.info(f"🔍 忘却候補の中期感情数: {len(expired)}")
    save_oblivion_intermediate_entries()
    logger.info("✅ [DONE] intermediate忘却処理が完了しました")

#shortカテゴリに関する忘却処理をまとめて呼び出す。
def run_short_oblivion_process():
    logger.info("📦 [START] short忘却プロセスの実行")
    expired = get_expired_short_term_emotions()
    logger.info(f"🔍 忘却候補の短期感情数: {len(expired)}")
    save_oblivion_short_entries()
    logger.info("✅ [DONE] short忘却処理が完了しました")


#emotion_index と emotion_data から、oblivion の日付に一致する履歴を削除する。
def run_index_and_data_removal_process():
    logger.info("🗑️ [START] インデックス・履歴削除プロセスを実行")
    remove_index_entries_by_date()
    remove_history_entries_by_date()
    logger.info("✅ [DONE] emotion_index / emotion_data からの履歴削除が完了しました")


#全体的な忘却プロセスの実行（順序制御あり）
def run_oblivion_cleanup_all():
    run_short_oblivion_process()
    run_intermediate_oblivion_process()
    run_index_and_data_removal_process()

    logger.info("🗑️ [START] oblivion期限付きデータの削除")
    delete_expired_oblivion_entries()
    delete_expired_short_oblivion_entries()
    logger.info("✅ [DONE] emotion_oblivion の古いデータを削除しました")


if __name__ == "__main__":
    run_oblivion_cleanup_all()
