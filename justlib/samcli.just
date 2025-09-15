# sam-cli utilities
#
# 必須環境変数:
# SAM_STACK_NAME
# SAM_PROFILE
#
# オプション環境変数:
# SAMOPT
# SAMTAGS
# SAMMIN
#

SAM_DEFAULT_TAGS := "author=blue21 provider=samcli.just"

_msg_info message:
    @echo "*🌻* samcli.just * {{message}}"

sam_default_conf:
    #!/usr/bin/env bash
    just _msg_info "Create samconfig.toml"
    cat<<EOF > samconfig.toml
    version = 0.1
    [default.global.parameters]
    stack_name = "{{SAM_STACK_NAME}}"
    [default.build.parameters]
    cached = true
    parallel = true
    [default.validate.parameters]
    lint = true
    [default.deploy.parameters]
    capabilities = "CAPABILITY_IAM"
    confirm_changeset = true
    resolve_s3 = true
    [default.package.parameters]
    resolve_s3 = true
    [default.sync.parameters]
    watch = true
    [default.local_start_api.parameters]
    warm_containers = "EAGER"
    [default.local_start_lambda.parameters]
    warm_containers = "EAGER"
    EOF

sam_build:
    @just _msg_info "Build Lambda"
    sam validate --lint
    sam build -u ${SAMOPT:-}

sam_deploy:
    @just _msg_info "Deploy Lambda"
    sam deploy ${SAMOPT:-} \
    --s3-prefix "{{SAM_STACK_NAME}}" \
    --profile {{SAM_PROFILE}} \
    --tags "{{SAM_DEFAULT_TAGS}} ${SAMTAGS:-}"

sam_delete:
    @just _msg_info "Delete Lambda"
    sam delete ${SAMOPT:-} \
    --profile {{SAM_PROFILE}}

sam_list:
    @just _msg_info "List stack outputs"
    sam list stack-outputs ${SAMOPT:-} \
    --profile {{SAM_PROFILE}}
    @just _msg_info "List resources"
    sam list resources ${SAMOPT:-} \
    --profile {{SAM_PROFILE}}
    @just _msg_info "List endpoints"
    sam list endpoints ${SAMOPT:-} \
    --profile {{SAM_PROFILE}}

sam_local_start:
    @just _msg_info "Local start API"
    sam local start-api ${SAMOPT:-}

sam_local_run:
    @just _msg_info "Local invoke Lambda"
    sam local invoke ${SAMOPT:-}

sam_remote_run:
    @just _msg_info "Remote invoke Lambda"
    sam remote invoke ${SAMOPT:-}

sam_tail:
    @just _msg_info "Tail logs"
    sam logs ${SAMOPT:-} \
    --profile {{SAM_PROFILE}} \
    --tail

sam_logs:
    @just _msg_info "Show logs for ${SAMMIN} minutes ago"
    sam logs ${SAMOPT:-} \
    --profile {{SAM_PROFILE}} \
    --start-time "${SAMMIN} minutes ago"
