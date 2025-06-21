# Yumia AI Response System

このリポジトリは、FastAPI を使って動作する感情生成型AI応答システムです。ユーザーとの対話から感情を抽出し、構造化されたデータとして記録・分類・応答を行います。

## 必要条件

- Python 3.9 以上
- pip（Pythonパッケージ管理ツール）

## インストール手順

1. **仮想環境の作成（任意）**

```bash
python -m venv venv
source venv/bin/activate  # Windows の場合: venv\Scripts\activate
```

2. **依存パッケージのインストール**

```bash
pip install -r requirements.txt
```

> ※ `requirements.txt` には以下のようなパッケージが含まれている必要があります：
> - fastapi
> - uvicorn
> - jsonlines
> - pydantic

## 実行

```bash
uvicorn main:app --reload
```

サーバーが起動したら、以下の URL にアクセスしてください：

- フロントエンドUI: [http://localhost:8000](http://localhost:8000)

## API エンドポイント

### `POST /chat`

ユーザーからのメッセージを受け取り、感情を解析して応答を返します。  

**送信形式（JSON）**
```json
{
  "message": "こんにちは"
}
```

**戻り値（JSON）**
```json
{
  "message": "AIによる応答",
  "history": [
    {"role": "user", "message": "こんにちは"},
    {"role": "system", "message": "AIによる応答"}
  ]
}
```

### `GET /history`

現在までの会話履歴を取得します（初期画面ロードなどに使用）。
