# SPDX-FileCopyrightText: Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
#
# SPDX-License-Identifier: BSD-3-Clause
""":py:class:`logging.Logger` setup and stream separation."""

import logging
import sys
import typing


# debug and info messages are written to sys.stdout
class _InfoFilter(logging.Filter):
    """Filter-class to delete any log-record with level above
    :any:`logging.INFO` **before** reaching the handler.
    """

    def __init__(self):
        super().__init__()

    def filter(self, record):
        return record.levelno <= logging.INFO


def setup(
    logger_name: str,
    format: str = "[%(levelname)s] %(message)s (%(name)s, %(asctime)s)",  # noqa: A002
    low_level_stream: typing.TextIO = sys.stdout,
    high_level_stream: typing.TextIO = sys.stderr,
) -> logging.Logger:
    """Return a logger object that is ready for console logging.

    Retrieves (as with :py:func:`logging.getLogger()`) the given logger, and
    then attaches 2 handlers (defined on the module) to it:

    1. A :py:class:`logging.StreamHandler` to output messages with level equal
       or lower than ``logging.INFO`` to the text-I/O stream
       ``low_level_stream``.  This is implemented by attaching a filter to the
       respective stream-handler to limit message records at this level.
    2. A :py:class:`logging.StreamHandler` to output warning, error messages
       and above to the text-I/O stream ``high_level_stream``, with an internal
       level set to ``logging.WARNING``.

    A new formatter, with the format string as defined by the ``format``
    argument is set on both handlers.  In this way, the global logger level can
    still be controlled from one single place.  If output is generated, then it
    is sent to the right stream.

    Parameters
    ----------
    logger_name
        The name of the module to generate logs for
    format
        The format of the logs, see :py:class:`logging.LogRecord` for more
        details. By default, the log contains the logger name, the log time,
        the log level and the massage.
    low_level_stream
        The stream where to output info messages and below
    high_level_stream
        The stream where to output warning messages and above

    Returns
    -------
        The configured logger. The same logger can be retrieved using the
        :py:func:`logging.getLogger` function.
    """

    logger = logging.getLogger(logger_name)

    formatter = logging.Formatter(format)

    handlers_installed = {k.name: k for k in logger.handlers}
    debug_logger_name = f"debug_info+{logger_name}"

    # First check that logger with a matching name or stream is not already
    # there before attaching a new one.
    if (debug_logger_name not in handlers_installed) or (
        getattr(handlers_installed[debug_logger_name], "stream") != low_level_stream
    ):
        debug_info = logging.StreamHandler(low_level_stream)
        debug_info.setLevel(logging.DEBUG)
        debug_info.setFormatter(formatter)
        debug_info.addFilter(_InfoFilter())
        debug_info.name = debug_logger_name
        logger.addHandler(debug_info)

    error_logger_name = f"warn_err+{logger_name}"

    # First check that logger with a matching name or stream is not already
    # there before attaching a new one.
    if (error_logger_name not in handlers_installed) or (
        getattr(handlers_installed[error_logger_name], "stream") != high_level_stream
    ):
        warn_err = logging.StreamHandler(high_level_stream)
        warn_err.setLevel(logging.WARNING)
        warn_err.setFormatter(formatter)
        warn_err.name = error_logger_name
        logger.addHandler(warn_err)

    return logger
