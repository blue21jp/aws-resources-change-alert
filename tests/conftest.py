"""テスト共通設定"""

# Standard Library
import os
from unittest.mock import MagicMock, patch

# Third Party Library
import pytest


@pytest.fixture(autouse=True)
def setup_env():
    """テスト用環境変数設定"""
    env_vars = {
        "SLACK_TOKEN_PARAM": "/test/slack/token",
        "SLACK_CHANNEL": "#test-channel",
        "BEDROCK_REGION": "us-east-1",
        "BEDROCK_MODEL_ID": "anthropic.claude-3-sonnet-20240229-v1:0",
        "AWS_DEFAULT_REGION": "us-east-1",
        "AWS_ACCESS_KEY_ID": "testing",
        "AWS_SECRET_ACCESS_KEY": "testing",
        "AWS_SECURITY_TOKEN": "testing",
        "AWS_SESSION_TOKEN": "testing",
    }

    with patch.dict(os.environ, env_vars):
        yield


@pytest.fixture
def mock_slack_client():
    """Slack WebClientのモック"""
    with patch("app.main.WebClient") as mock_client:
        mock_slack = MagicMock()
        mock_slack.chat_postMessage.return_value = {"ok": True}
        mock_client.return_value = mock_slack
        yield mock_slack
