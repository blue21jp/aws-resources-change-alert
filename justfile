# justfile for AWS Resource Change Alert
#
# オプション環境変数:
#   PROFILE            - AWSプロファイル名 (デフォルト: "dummy")

# local変数
PROFILE := env_var_or_default("PROFILE", "dummy")

# Python関連の環境変数
export PYPROJECT := `basename $PWD`
export REQUIREMENTS_TXT := "app/requirements.txt"

# samcli関連の環境変数
export SAM_STACK_NAME := PYPROJECT
export SAM_PROFILE := PROFILE

# justlibをインポート
import 'justlib/python.just'
import 'justlib/samcli.just'
import 'justlib/act.just'

#---------------------------
# Lambda Deploy
#---------------------------

build:
    just pylint
    just poetry_export
    just sam_build

deploy:
    just sam_deploy

delete:
    just sam_delete

#---------------------------
# Lambda Test
#---------------------------

run:
    #!/usr/bin/env bash
    export SAMOPT="-e events/event.json \
    -n env.json \
    --profile $SAM_PROFILE"
    just sam_local_run

remote-run:
    #!/usr/bin/env bash
    export SAMOPT="--event-file events/event.json \
    --profile $SAM_PROFILE"
    just sam_remote_run

#---------------------------
# SSM Parameter
#---------------------------

slack-token-register:
    #!/usr/bin/env bash
    echo "SSMパラメータにSlackトークンを登録します"
    aws ssm put-parameter \
      --name "/resources-change-alert/slack/bot-token" \
      --value "$(cat slack/slack_token)" \
      --type SecureString \
      --overwrite \
      --profile {{PROFILE}}

slack-token-delete:
    #!/usr/bin/env bash
    echo "Slackトークンを削除中..."
    aws ssm delete-parameter \
      --name "/resources-change-alert/slack/bot-token" \
      --profile {{PROFILE}}

#---------------------------
# GitHub Actions
#---------------------------

GHA_STACK_NAME := "aws-resources-change-alert-gha"

# GitHub Actions用IAMロールをデプロイ
# build不要
gha-role-deploy:
    #!/usr/bin/env bash
    export SAMOPT="--template-file github-actions-role.yml --stack-name {{GHA_STACK_NAME}}"
    just sam_deploy

# GitHub Actions用IAMロールを削除
gha-role-delete:
    #!/usr/bin/env bash
    export SAMOPT="--stack-name {{GHA_STACK_NAME}}"
    just sam_delete

# PROFILE=sandbox just act
act_deploy:
    #!/usr/bin/env bash
    ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text --profile {{PROFILE}})
    export ACT_IAM_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/{{GHA_STACK_NAME}}"
    export ACT_WORKFLOW="gha/deploy.yml"
    export ACT_PROFILE="{{PROFILE}}"
    just act-run
