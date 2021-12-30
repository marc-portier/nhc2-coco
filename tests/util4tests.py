import logging
import logging.config
import os
import sys
import yaml
import pytest
from dotenv import load_dotenv


log = logging.getLogger("tests")


def random_passwd(len=10):
    return ''.join(random.choices(string.digits + string.ascii_lowercase, k=len))


def enable_test_logging():
    load_dotenv()
    if 'PYTEST_LOGCONF' in os.environ:
        logconf = os.environ['PYTEST_LOGCONF']
        with open(logconf, 'r') as yml_logconf:
            logging.config.dictConfig(yaml.load(yml_logconf, Loader=yaml.SafeLoader))
        log.info(f"Logging enabled according to config in {logconf}")


def run_single_test(testfile):
    enable_test_logging()
    log.info(
        f"Running tests in {testfile} " +
        "with -v(erbose) and -s(no stdout capturing) " +
        "and logging to stdout, level controlled by env var ${PYTEST_LOGCONF}")
    sys.exit(pytest.main(["-v", "-s",  testfile]))
