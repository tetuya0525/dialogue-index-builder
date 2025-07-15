# ==============================================================================
# Dockerfile
# ==============================================================================
# ベースイメージ: Python 3.12-slim
FROM python:3.12-slim

# 環境変数: Pythonログのバッファリングを無効化
ENV PYTHONUNBUFFERED True

# 作業ディレクトリを設定
WORKDIR /app

# 依存関係をインストール
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ソースコードをコピー
COPY . .

# Cloud RunのPORT環境変数を設定
ENV PORT 8080

# エントリーポイント
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "3", "--timeout", "120", "main:app"]
