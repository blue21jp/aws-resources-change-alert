"""
AWS CloudTrail イベント通知システム

CloudTrailイベントを受信し、Bedrockで解析してSlackに通知するLambda関数
"""

# Standard Library
import json
import os

# Third Party Library
import boto3
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.parameters import get_parameter
from aws_lambda_powertools.utilities.typing import LambdaContext
from slack_sdk import WebClient

# ロガー設定
logger = Logger(service="aws-resources-change-alert")

# プロンプトテンプレート
BEDROCK_PROMPT_TEMPLATE = """
あなたは、AWS CloudTrailのイベントデータを解説する専門家です。
event dataをもとに、非エンジニア向けの簡潔な解説を日本語で作成して。

## event data
{event_data}

回答は下記の書式に従いSlack投稿用に生成すること。

*イベント要約*

*検出日時(JST)*

*アカウントID*

*リージョン*

*リソース情報*

*実行者情報*

*想定されるリスク*
最大２件を箇条書き
"""


def generate_notification_message(event: dict) -> str:
    """CloudTrailイベントから通知メッセージを生成する

    Args:
        event (dict): CloudTrailイベントデータ

    Returns:
        str: 生成された通知メッセージ
    """
    try:
        bedrock = boto3.client(
            "bedrock-runtime", region_name=os.environ["BEDROCK_REGION"]
        )
        model_id = os.environ["BEDROCK_MODEL_ID"]
        prompt = BEDROCK_PROMPT_TEMPLATE.format(
            event_data=json.dumps(event, indent=2, ensure_ascii=False)
        )

        response = bedrock.invoke_model(
            modelId=model_id,
            body=json.dumps(
                {"messages": [{"role": "user", "content": [{"text": prompt}]}]}
            ),
            contentType="application/json",
            accept="application/json",
        )
        body = json.loads(response["body"].read().decode("utf-8"))

        # レスポンス構造の検証
        if "output" not in body or "message" not in body["output"]:
            raise ValueError("Bedrockレスポンス構造が不正です")

        return str(body["output"]["message"]["content"][0]["text"])
    except Exception as e:
        logger.exception(f"Bedrockエラー: {e}")
        return f"*Bedrockエラーが発生しました*\n\n*イベントデータ*\n```\n{json.dumps(event, indent=2, ensure_ascii=False)}\n```"


def send_slack_notification(message: str) -> dict:
    """Slackに通知を送信する

    Args:
        message (str): 通知メッセージ

    Returns:
        dict: 処理結果
    """
    logger.debug(message)

    token = get_parameter(os.environ["SLACK_TOKEN_PARAM"], decrypt=True)
    channel = os.environ["SLACK_CHANNEL"]
    client = WebClient(token=token)
    try:
        response = client.chat_postMessage(
            channel=channel,
            text=f"AWS CloudTrail アラート\n{message}",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*AWS CloudTrail アラート*",
                    },
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": message},
                },
            ],
        )
        if response["ok"]:
            logger.info(f"Slack通知成功: {channel}")
            return {"statusCode": 200, "message": "通知成功"}
        else:
            logger.error(
                f"Slack通知失敗: {response.get('error', '不明なエラー')}"
            )
            return {"statusCode": 500, "message": "通知失敗"}
    except Exception as e:
        logger.exception(f"Slack通知エラー: {e}")
        return {"statusCode": 500, "message": f"Slack通知エラー: {e}"}


@logger.inject_lambda_context
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """Lambdaハンドラー関数

    Args:
        event (dict): イベントデータ
        context (Any): ランタイム情報

    Returns:
        dict: 処理結果
    """
    logger.info("処理開始")
    try:
        # 必須環境変数チェック
        required_vars = [
            "SLACK_TOKEN_PARAM",
            "SLACK_CHANNEL",
            "BEDROCK_REGION",
            "BEDROCK_MODEL_ID",
        ]
        for var in required_vars:
            if not os.environ.get(var):
                raise ValueError(f"環境変数 {var} が設定されていません")

        # EventBridge経由の場合、CloudTrailデータはdetailに格納
        cloudtrail_event = event.get("detail", event)
        message = generate_notification_message(cloudtrail_event)
        return send_slack_notification(message)
    except Exception as e:
        logger.exception(f"処理エラー: {e}")
        return {"statusCode": 500, "message": f"処理エラー: {e}"}
