"""app.pyのテストコード"""

# Standard Library
import json
from unittest.mock import MagicMock, patch

# Third Party Library
import pytest
from moto import mock_aws
from slack_sdk.errors import SlackApiError

# First Party Library
from app.main import (
    generate_notification_message,
    lambda_handler,
    send_slack_notification,
)


class TestGenerateNotificationMessage:
    """通知メッセージ生成のテスト"""

    def test_success(self):
        """正常系: メッセージ生成成功"""
        mock_response = {
            "output": {
                "message": {
                    "content": [{"text": "*イベント要約*\nテストイベント"}]
                }
            }
        }

        with patch("boto3.client") as mock_client:
            mock_bedrock = MagicMock()
            mock_bedrock.invoke_model.return_value = {
                "body": MagicMock(
                    read=lambda: json.dumps(mock_response).encode()
                )
            }
            mock_client.return_value = mock_bedrock

            event = {
                "eventName": "CreateUser",
                "userIdentity": {"type": "IAMUser"},
            }
            result = generate_notification_message(event)

            assert "*イベント要約*" in result
            mock_bedrock.invoke_model.assert_called_once()

    def test_bedrock_error(self):
        """異常系: Bedrockエラー"""
        with patch("boto3.client") as mock_client:
            mock_bedrock = MagicMock()
            mock_bedrock.invoke_model.side_effect = Exception("Bedrockエラー")
            mock_client.return_value = mock_bedrock

            event = {"eventName": "CreateUser"}
            result = generate_notification_message(event)

            assert "*Bedrockエラーが発生しました*" in result
            assert "CreateUser" in result


class TestSendSlackNotification:
    """Slack通知のテスト"""

    @mock_aws
    def test_success(self, mock_slack_client):
        """正常系: Slack通知成功"""
        # Third Party Library
        import boto3

        ssm = boto3.client("ssm", region_name="us-east-1")
        ssm.put_parameter(
            Name="/test/slack/token",
            Value="xoxb-test-token",
            Type="SecureString",
        )

        result = send_slack_notification("テストメッセージ")

        assert result["statusCode"] == 200
        mock_slack_client.chat_postMessage.assert_called_once()

    @mock_aws
    def test_slack_api_error(self):
        """異常系: Slack APIエラー"""
        # Third Party Library
        import boto3

        ssm = boto3.client("ssm", region_name="us-east-1")
        ssm.put_parameter(
            Name="/test/slack/token",
            Value="xoxb-test-token",
            Type="SecureString",
        )

        with patch("app.main.WebClient") as mock_client:
            mock_slack = MagicMock()
            mock_slack.chat_postMessage.side_effect = SlackApiError(
                "API Error", response={"error": "invalid_auth"}
            )
            mock_client.return_value = mock_slack

            result = send_slack_notification("テストメッセージ")

            assert result["statusCode"] == 500


class TestLambdaHandler:
    """Lambdaハンドラーのテスト"""

    @mock_aws
    def test_success(self, mock_slack_client):
        """正常系: 処理成功"""
        # Third Party Library
        import boto3

        ssm = boto3.client("ssm", region_name="us-east-1")
        ssm.put_parameter(
            Name="/test/slack/token",
            Value="xoxb-test-token",
            Type="SecureString",
        )

        mock_bedrock_response = {
            "output": {
                "message": {
                    "content": [{"text": "*イベント要約*\nテストイベント"}]
                }
            }
        }

        with patch("boto3.client") as mock_boto_client:
            mock_bedrock = MagicMock()
            mock_bedrock.invoke_model.return_value = {
                "body": MagicMock(
                    read=lambda: json.dumps(mock_bedrock_response).encode()
                )
            }
            mock_boto_client.return_value = mock_bedrock

            event = {
                "detail": {
                    "eventName": "CreateUser",
                    "userIdentity": {"type": "IAMUser"},
                }
            }
            context = MagicMock()

            result = lambda_handler(event, context)

            assert result["statusCode"] == 200

    def test_missing_env_var(self):
        """異常系: 環境変数不足"""
        with patch.dict("os.environ", {}, clear=True):
            event = {"detail": {"eventName": "CreateUser"}}
            context = MagicMock()

            result = lambda_handler(event, context)

            assert result["statusCode"] == 500
            assert "環境変数" in result["message"]

    @pytest.mark.parametrize(
        "event_structure",
        [{"detail": {"eventName": "CreateUser"}}, {"eventName": "CreateUser"}],
    )
    @mock_aws
    def test_event_structures(self, event_structure, mock_slack_client):
        """パラメータ化テスト: 異なるイベント構造"""
        # Third Party Library
        import boto3

        ssm = boto3.client("ssm", region_name="us-east-1")
        ssm.put_parameter(
            Name="/test/slack/token",
            Value="xoxb-test-token",
            Type="SecureString",
        )

        mock_bedrock_response = {
            "output": {
                "message": {
                    "content": [{"text": "*イベント要約*\nテストイベント"}]
                }
            }
        }

        with patch("boto3.client") as mock_boto_client:
            mock_bedrock = MagicMock()
            mock_bedrock.invoke_model.return_value = {
                "body": MagicMock(
                    read=lambda: json.dumps(mock_bedrock_response).encode()
                )
            }
            mock_boto_client.return_value = mock_bedrock

            context = MagicMock()
            result = lambda_handler(event_structure, context)

            assert result["statusCode"] == 200
