# AI動画生成アプリ

テキストプロンプトから短いMP4動画を生成するシンプルなWebアプリです。

## 機能
- プロンプト入力でシーン画像を自動生成（`OPENAI_API_KEY` がある場合は `gpt-image-1` を利用）
- APIキー未設定時はフォールバック画像を自動作成
- 生成した画像をつなげてMP4を書き出し
- ブラウザから動画生成・プレビュー再生・ダウンロード

## セットアップ

### Linux (bash / zsh)
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn main:app --reload
```

### macOS (bash / zsh)
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn main:app --reload
```

### Windows (PowerShell)
```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn main:app --reload
```

### Windows (cmd.exe)
```bat
py -3 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn main:app --reload
```

ブラウザで `http://127.0.0.1:8000` を開いてください。

## 環境変数
- `OPENAI_API_KEY`（任意）: 設定するとAI画像生成を利用

## 注意
- 初回は動画エンコードのために少し時間がかかります。
- サーバー上では `generated/` 配下に動画が保存されます。
