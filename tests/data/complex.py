import logging

logger = logging.getLogger("clapper_test.config_with_logs")

logger.debug("Debug level message")
logger.info("Info level message")
logger.warning("Warning level message")
logger.error("Error level message")

cplx = dict(
    a="test",
    b=42,
    c=3.14,
    d=[1, 2, 37],
)
