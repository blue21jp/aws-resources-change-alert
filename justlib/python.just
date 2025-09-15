# Python utilities
#
# 必須環境変数:
#   REQUIREMENTS_TXT - requirements.txtファイルパス
#   PYPROJECT        - プロジェクト名
#
# オプション環境変数:
#   PYOPT            - pytestオプション (デフォルト: 空文字列)

_py_msg_info message:
    @echo "*🐍* python.just * {{message}}"

pyinit:
    @just _py_msg_info "Creating new project in ./pyproject.toml"
    @just _py_msg_info "Change the python version. default is 3.12"
    @just _py_msg_info "Change the dependency module."
    envsubst < ./justlib/pyproject.default.toml > ./pyproject.toml
    cp ./justlib/.tools-versions.template ./.tools-versions
    mkdir -p tests
    touch tests/__init__.py

pyinstall:
    poetry install

pylint:
    poetry run isort .
    poetry run black .
    poetry run pflake8 .
    poetry run mypy --install-types --non-interactive .
    poetry run vulture .

pytest:
    poetry run python -m pytest -vv --log-cli-level INFO ${PYOPT:-}

pytest-cov:
    poetry run python -m pytest --cov ${PYOPT:-}

pysecurity-check:
    @echo "****** bandit"
    -poetry run bandit -r app/ --severity-level low
    @echo
    @echo "****** pip-audit"
    -poetry run pip-audit
    @echo
    @echo "****** bandit (High severity only - will fail on error)"
    poetry run bandit -r app/ --severity-level high

poetry_export:
    poetry export -f requirements.txt --without-hashes -o ${REQUIREMENTS_TXT}

pyclean:
    poetry env remove --all
    -find . -name '__pycache__' -exec rm -rf {} +
    -find . -name '.mypy_cache' -exec rm -rf {} +
    -find . -name '*.pyc' -exec rm -f {} +
    -find . -name '*.pyo' -exec rm -f {} +
    -rm -rf .pytest_cache .coverage
    -rm -rf dist build *.egg-info .aws-sam
    -rm -f poetry.lock
