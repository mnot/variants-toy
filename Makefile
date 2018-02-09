
TESTS = $(wildcard test_*.json)

all: ${TESTS}
	python2 ./variants.py ${TESTS}