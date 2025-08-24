# ==============================================================================
# Memory Library - Dialogue Index Builder Service
# main.py
#
# Role:         対話ログ(articles)を分析し、高速検索・閲覧用の
#               対話インデックス(dialogue_index)を生成・更新する。
# Trigger:      API Gateway経由のHTTP POSTリクエスト
# Version:      1.0
# Author:       心理 (Thinking Partner)
# Last Updated: 2025-07-16
# ==============================================================================
import os
from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import firestore
from datetime import datetime, timedelta, timezone

# --- 初期化 (Initialization) ---
try:
    firebase_admin.initialize_app()
    db = firestore.client()
except ValueError:
    pass

app = Flask(__name__)


# --- メインロジック ---
@app.route("/", methods=["POST"])
def build_index():
    """
    対話インデックスの構築・更新を実行するメイン関数。
    """
    app.logger.info("対話インデックス構築処理を開始します。")

    try:
        # 現時点では、全ての対話ログを対象にインデックスを再構築する
        # 将来的には、リクエストで日付範囲を指定できるように拡張可能
        dialogue_logs = (
            db.collection("articles").where("sourceType", "==", "DIALOGUE_LOG").stream()
        )

        # 日付ごとに対話ログをグループ化
        logs_by_date = {}
        for log in dialogue_logs:
            log_data = log.to_dict()
            # createdAtがTimestamp型であることを想定
            created_at_dt = log_data.get("createdAt")
            if not created_at_dt:
                continue

            # タイムゾーンをJST (+9)と仮定して日付を取得
            jst_date_str = (
                created_at_dt.astimezone(timezone(timedelta(hours=9)))
            ).strftime("%Y-%m-%d")

            if jst_date_str not in logs_by_date:
                logs_by_date[jst_date_str] = []

            # articleIdをドキュメントデータに追加して保存
            log_data["id"] = log.id
            logs_by_date[jst_date_str].append(log_data)

        app.logger.info(f"{len(logs_by_date)}日分の対話ログを処理します。")

        # 日付ごとにインデックスを生成
        for date_str, logs in logs_by_date.items():
            process_daily_logs(date_str, logs)

        return (
            jsonify(
                {
                    "status": "success",
                    "message": f"{len(logs_by_date)}日分のインデックスを更新しました。",
                }
            ),
            200,
        )

    except Exception as e:
        app.logger.error(f"インデックス構築中に予期せぬエラーが発生しました: {e}")
        return jsonify({"status": "error", "message": "Internal Server Error"}), 500


def process_daily_logs(date_str, logs):
    """
    一日分の対話ログを処理し、インデックスドキュメントを生成・更新する。
    """
    app.logger.info(f"{date_str} のインデックスを生成中...")

    # ★★★【AI分析シミュレーション】★★★
    # 将来的に、ここでGemini APIなどを呼び出し、
    # 1日の要約や時間帯ごとの分析を行う。
    # 現段階では、固定のダミーデータを生成する。

    # 1. 1日のサマリーを生成 (AI)
    daily_summary = (
        f"{date_str}の対話要約。この日は{len(logs)}件の対話記録がありました。"
    )

    # 2. 時間帯ごとのチャンクを生成 (3時間区切りと仮定)
    time_chunks = []
    # (シミュレーションのため、ダミーのチャンクを1つ生成)
    first_log = logs[0]  # 代表として最初のログを使用

    chunk = {
        "startTime": "10:00",
        "endTime": "12:59",
        "chunkSummary": "AI司書の設計に関する議論が行われました。",
        "categories": ["システム設計", "バックエンド"],  # (AIによる分析結果)
        "tags": ["Cloud Run", "Firestore", "API設計"],  # (AIによる分析結果)
        "keyMoments": [
            {
                "topic": "最初のキーモーメントのトピック",
                "timestamp": "10:15",  # (AIによる特定)
                "articleId": first_log.get("id", ""),
                "articleTitle": first_log.get("title", "無題の対話ログ"),
            }
        ],
    }
    time_chunks.append(chunk)

    # 3. Firestoreに書き込むデータを作成
    index_doc_data = {
        "date": datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc),
        "dailySummary": daily_summary,
        "timeChunks": time_chunks,
        "updatedAt": firestore.SERVER_TIMESTAMP,
    }

    # 4. Firestoreに書き込み (set with merge=Trueで更新)
    doc_ref = db.collection("dialogue_index").document(date_str)
    doc_ref.set(index_doc_data, merge=True)

    app.logger.info(f"{date_str} のインデックスをFirestoreに保存しました。")


# Gunicornから直接実行されるためのエントリーポイント
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
