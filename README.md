# AWS Resources Change Alert

AWS CloudTrailイベントを監視し、重要なリソース変更をSlackに通知するサーバーレスアプリケーション

## このリポジトリについて

このリポジトリは参考用として公開しています。  
Pull Request や Issue への対応は行いません。

## 概要

このシステムは、AWS環境でのリソース変更を自動的に検知し、Amazon Bedrock（Nova Premier）を使用して分かりやすい日本語の解説を生成してSlackに通知します。

### 主な機能

- IAMユーザーの作成・削除・権限変更の監視
- Amazon Bedrock Nova Premierによる変更内容の自動解析・解説
- Slackへのリアルタイム通知

## アーキテクチャ

<img src="generated-diagrams/architecture.png" alt="Architecture Diagram" width="600">

- **AWS Lambda**: CloudTrailイベント処理とSlack通知（Python 3.13）
- **Amazon EventBridge**: CloudTrailイベントのルーティング
- **Amazon Bedrock**: Nova Premierモデルによる自然言語解析
- **AWS Systems Manager Parameter Store**: Slackトークンの安全な保存
- **AWS CloudWatch Logs**: ログ管理（保持期間1日）

## 前提条件

- AWS CloudTrailが有効化されていること
- SlackAppを用意し、Bot Tokenを作成していること
  - slack/app_manifest.json参照

## ローカル環境の必須ツール

- aws-cli (v2)
- sam-cli
- docker
- just
- mise (Python/Poetryバージョン管理)
- poetry

注) OSは`Ubuntu24.04`を使用しています。

## ローカル環境のセットアップ

### 1. 環境準備

```bash
# Pythonとpoetryのセットアップ
mise install
poetry install
```

### 2. Slackトークン設定

```bash
# Slackトークンファイルを作成
echo "xoxb-your-slack-bot-token" > slack/slack_token

# SSMパラメータに登録
PROFILE=sandbox just slack-token-register
```

### 3. デプロイ

```bash
# ビルドとデプロイ
just build
PROFILE=sandbbox just deploy
```

### 4. 削除

```bash
# スタック削除
just delete

# Slackトークン削除
just slack-token-delete
```

## 設定

### 環境変数

- `PROFILE`: AWSプロファイル名 (デフォルト: "dummy")

### Lambda環境変数

- `SLACK_TOKEN_PARAM`: "/resources-change-alert/slack/bot-token"
- `SLACK_CHANNEL`: "#general"
- `BEDROCK_REGION`: デプロイリージョン
- `BEDROCK_MODEL_ID`: "us.amazon.nova-premier-v1:0"

### 監視対象イベント

現在監視中:
- IAMユーザーの作成・削除
- IAMポリシーのアタッチ・デタッチ

コメントアウト中（サンプル）:
- ネットワーク設定変更
- RDS設定変更

## 開発

### コード品質チェック

```bash
# リンター・フォーマッター実行
just pylint
```

### 単体テスト実行

```bash
# テスト実行
poetry run pytest
```


### Lambdaローカル実行

```bash
# ローカルでのテスト実行
PROFILE=sandbox just run
```

### Lambdaリモート実行

```bash
# デプロイ済みLambdaでのテスト実行
PROFILE=sandbox just remote-run
```

### GitHub Actionsローカル実行

GithubActionsでデプロイできます。  
下記はactを使用してローカル実行する方法です。

```bash
# GitHub Actions用IAMロールをデプロイ
PROFILE=sandbox just gha-role-deploy

# GitHub Actionsワークフローをローカル実行
PROFILE=sandbox just act_deploy

# GitHub Actions用IAMロールを削除
PROFILE=sandbox just gha-role-delete
```

注) Githubでは動作確認していない。
