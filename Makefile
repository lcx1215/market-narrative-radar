.PHONY: start restart stop status test test-provider clean validate

start:
	python3 scripts/mnr.py start

restart:
	python3 scripts/mnr.py start --restart

stop:
	python3 scripts/mnr.py stop

status:
	python3 scripts/mnr.py status

test:
	python3 scripts/mnr.py test

test-provider:
	python3 scripts/mnr.py test --provider

clean:
	python3 scripts/mnr.py clean

validate:
	python3 scripts/validate_project.py
