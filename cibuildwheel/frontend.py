from __future__ import annotations

import shlex
import typing
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, get_args

from .logger import log
from .util.helpers import parse_key_value_string

BuildFrontendName = Literal["pip", "build", "build[uv]"]


@dataclass(frozen=True)
class BuildFrontendConfig:
    name: BuildFrontendName
    args: Sequence[str] = ()

    @staticmethod
    def from_config_string(config_string: str) -> BuildFrontendConfig:
        config_dict = parse_key_value_string(config_string, ["name"], ["args"])
        name = " ".join(config_dict["name"])
        if name not in get_args(BuildFrontendName):
            names = ", ".join(repr(n) for n in get_args(BuildFrontendName))
            msg = f"Unrecognised build frontend {name!r}, must be one of {names}"
            raise ValueError(msg)

        name = typing.cast(BuildFrontendName, name)

        args = config_dict.get("args") or []
        return BuildFrontendConfig(name=name, args=args)

    def options_summary(self) -> str | dict[str, str]:
        if not self.args:
            return self.name
        else:
            return {"name": self.name, "args": repr(self.args)}


def _get_verbosity_flags(level: int, frontend: BuildFrontendName) -> list[str]:
    if frontend == "pip":
        if level > 0:
            return ["-" + level * "v"]
        if level < 0:
            return ["-" + -level * "q"]
    elif not 0 <= level < 2:
        msg = f"build_verbosity {level} is not supported for {frontend} frontend. Ignoring."
        log.warning(msg)
    return []


def _split_config_settings(config_settings: str) -> list[str]:
    config_settings_list = shlex.split(config_settings)
    return [f"-C{setting}" for setting in config_settings_list]


def get_build_frontend_extra_flags(
    build_frontend: BuildFrontendConfig, verbosity_level: int, config_settings: str
) -> list[str]:
    return [
        *_split_config_settings(config_settings),
        *build_frontend.args,
        *_get_verbosity_flags(verbosity_level, build_frontend.name),
    ]
