.PHONY: _base init test #see http://www.gnu.org/software/make/manual/html_node/Phony-Targets.html
_base:
	@poetry --quiet  # just check / assert that poetry is available

init: _base
	@poetry update

test: _base
	@poetry run pytest
