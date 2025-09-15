# GitHub Actions local testing utilities
#
# 必須環境変数:
#   ACT_PROFILE      - AWSプロファイル(user)
#   ACT_IAM_ROLE_ARN - IAMロールARN
#   ACT_WORKFLOW     - GitHub Actions Workflow名
#
# オプション環境変数:
#   ACTOPT          - actコマンドオプション (デフォルト: 空文字列)
#

# GitHub Actions をローカルでテスト実行
act-run:
    #!/usr/bin/env bash
    set -euo pipefail

    # ACT_IAM_ROLE_ARNが設定されている場合のみaws-tmp-credsを実行
    if [ -n "${ACT_IAM_ROLE_ARN:-}" ]; then
        just aws-tmp-creds
        ENV_FILE_OPT="--env-file env_aws"
    else
        ENV_FILE_OPT=""
    fi

    act -P ubuntu-latest=catthehacker/ubuntu:act-latest \
        --container-architecture linux/amd64 \
        -W ${ACT_WORKFLOW} ${ACTOPT:-} \
        --secret-file gha/.secrets \
        ${ENV_FILE_OPT} || true

    # env_awsファイルが存在する場合のみ削除
    [ -f env_aws ] && rm -f env_aws || true

# AWS一時認証情報を生成
aws-tmp-creds:
    #!/usr/bin/env bash
    set -euo pipefail
    aws sts assume-role \
        --role-arn "${ACT_IAM_ROLE_ARN}" \
        --role-session-name act-test \
        --duration-seconds 1800 \
        --profile $ACT_PROFILE \
        --query 'Credentials' \
        | jq -r '.|[.AccessKeyId,.SecretAccessKey,.SessionToken]|@csv' \
        | awk -F, '{printf("AWS_ACCESS_KEY_ID=%s\nAWS_SECRET_ACCESS_KEY=%s\nAWS_SESSION_TOKEN=%s\nAWS_DEFAULT_REGION=us-east-1\n",$1,$2,$3)}' \
        > env_aws
