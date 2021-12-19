# variables
PYMODULE = nhc2_coco
FLAKE8_EXCLUDE = venv,.venv,.eggs,.tox,.git,__pycache__,*.pyc


# declare non-file based targets see http://www.gnu.org/software/make/manual/html_node/Phony-Targets.html
.PHONY: _base init test check run

# make targets
_base:
	@poetry --quiet  # just check / assert that poetry is available

init: _base
	@poetry update

check: _base
	@poetry run flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude ${FLAKE8_EXCLUDE}
	@poetry run flake8 . --count --exit-zero --max-complexity=10 --max-line-length=132 --statistics --exclude ${FLAKE8_EXCLUDE}

test: _base
	@poetry run pytest
