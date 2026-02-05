import abc
import logging
from enum import Enum
from pathlib import Path

import colorlog
from pydantic import BaseModel, Field, field_validator, model_validator
from typing_extensions import Self

LOG_COLORS = {
    "DEBUG": "white",
    "INFO": "bold_green",
    "WARNING": "bold_yellow",
    "ERROR": "bold_red",
    "CRITICAL": "bold_white,bg_red",
}
COLORED_FORMATTER = colorlog.ColoredFormatter(
    "%(bold_black)s%(asctime)s%(reset)s "
    "%(log_color)s%(levelname)s%(reset)s "
    "%(cyan)s%(name)s%(reset)s - "
    "%(light_white)s%(message)s%(reset)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    log_colors=LOG_COLORS,
    style="%",
)
REGULAR_FORMATTER = logging.Formatter(
    "%(asctime)s %(levelname)s %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    style="%",
)


class LoggerHandlerType(Enum):
    STREAM = 1
    FILE = 2


class SetupLoggerParams(BaseModel):
    level: str
    handler_types: set[LoggerHandlerType] = Field(default_factory=set)
    file_path: Path | None = None

    @field_validator("level")
    @classmethod
    def validate_log_level_string(cls, value: str) -> str:
        # logging.logging.getLevelNamesMapping() is not being used here because
        # it's new in Python 3.11
        valid_levels = logging._nameToLevel
        if value.upper() not in valid_levels:
            msg = f"'level' must be one of: {valid_levels}. Got '{value}'."
            raise ValueError(msg)
        return value.upper()

    @model_validator(mode="after")
    def validate_file_path(self) -> Self:
        uses_file_handler = LoggerHandlerType.FILE in self.handler_types
        if uses_file_handler and self.file_path is None:
            msg = (
                "'file_path' must be provided when 'FILE' handler is specified  in `handler_types`."
            )
            raise ValueError(msg)

        if not uses_file_handler and self.file_path is not None:
            msg = "'file_path' cannot be provided when 'FILE' handler "
            "is not specified in `handler_types`."
            raise ValueError(msg)

        return self


class LoggerHandlerCreator(abc.ABC):
    """Abstract base class for logger handler creators."""

    @abc.abstractmethod
    def create(self, params: SetupLoggerParams) -> logging.Handler: ...


class ColoredStreamHandlerCreator(LoggerHandlerCreator):
    def create(self, _params: SetupLoggerParams) -> logging.Handler:
        handler = colorlog.StreamHandler()
        formatter = COLORED_FORMATTER
        handler.setFormatter(formatter)
        return handler


class FileHandlerCreator(LoggerHandlerCreator):
    def create(self, params: SetupLoggerParams) -> logging.FileHandler:
        if not params.file_path:
            msg = "'file_path' must be provided for FileHandler."
            raise ValueError(msg)
        if not params.file_path.parent.exists():
            raise FileNotFoundError(params.file_path)
        file_handler = logging.FileHandler(params.file_path)
        file_formatter = REGULAR_FORMATTER
        file_handler.setFormatter(file_formatter)
        return file_handler


LOGGER_HANDLER_TO_CREATOR: dict[LoggerHandlerType, LoggerHandlerCreator] = {
    LoggerHandlerType.STREAM: ColoredStreamHandlerCreator(),
    LoggerHandlerType.FILE: FileHandlerCreator(),
}


def add_logger_handlers(logger: logging.Logger, params: SetupLoggerParams) -> None:
    for logger_handler_type in params.handler_types:
        if logger_handler_type not in LOGGER_HANDLER_TO_CREATOR:
            error_message = f"Unsupported logger handler type: {logger_handler_type}"
            raise ValueError(error_message)
        handler = LOGGER_HANDLER_TO_CREATOR[logger_handler_type].create(params)
        if not isinstance(handler, logging.Handler):
            error_message = f"Expected logging.Handler, got {type(handler).__name__}"
            raise TypeError(error_message)
        logger.addHandler(handler)


def setup_logger(params: SetupLoggerParams) -> None:
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.setLevel(params.level)
    add_logger_handlers(root_logger, params)
