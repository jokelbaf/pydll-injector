import argparse
import logging
import sys
import pathlib
import typing

import tomli
import pydantic

from pydll_injector.process import spawn_process, is_process_running, terminate_process
from pydll_injector.models import Launcher, Environment

logger = logging.getLogger(__name__)

class LauncherConfig(pydantic.BaseModel):
    executable_file: pathlib.Path
    cmd_line_args: typing.Optional[str] = None
    dll_list: typing.List[pathlib.Path]
    injection_method: typing.Literal["standard", "apc", "nt", "hook"] = "standard"

class EnvironmentConfig(pydantic.BaseModel):
    vars: typing.Optional[typing.List[str]] = None
    use_system_env: bool = True
    environment_append: bool = False

class Config(pydantic.BaseModel):
    launcher: LauncherConfig
    environment: EnvironmentConfig


def load_config(path: pathlib.Path) -> Config:
    """Load and validate TOML config at `path`."""
    try:
        with path.open("rb") as f:
            raw = tomli.load(f)
    except Exception as e:
        logger.error(f"Failed to read config file {path!s}: {e}")
        sys.exit(1)

    try:
        return Config.model_validate(raw)
    except pydantic.ValidationError as ve:
        logger.error("Configuration validation error:\n%s", ve)
        sys.exit(1)

def parse_args() -> argparse.Namespace:
    """Define and parse CLI arguments."""
    parser = argparse.ArgumentParser(prog="pydll-injector", description="Inject DLLs into a process.")
    parser.add_argument(
        "-c", "--config", type=pathlib.Path, default=None,
        help="Path to a TOML config file (overrides default config.toml lookup)"
    )
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error", "critical"],
        default="info",
        help="Set the logging level (default: info)"
    )
    parser.add_argument(
        "-e", "--executable-file", type=pathlib.Path,
        help="Path to the executable to launch"
    )
    parser.add_argument(
        "--cmd-line-args", type=str,
        help="Command-line arguments to pass to the executable"
    )
    parser.add_argument(
        "--dll-list", nargs="+", type=pathlib.Path,
        help="One or more DLL paths to inject"
    )
    parser.add_argument(
        "--injection-method", choices=["standard", "apc", "nt", "hook"],
        help="Injection method (default: standard)"
    )
    parser.add_argument(
        "--vars", nargs="+",
        help="Environment variables for the DLLs (e.g. FOO=bar BAZ=qux)"
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--use-system-env", dest="use_system_env", action="store_true",
        help="Include system environment variables (default)"
    )
    group.add_argument(
        "--no-use-system-env", dest="use_system_env", action="store_false",
        help="Do NOT include system environment variables"
    )
    parser.set_defaults(use_system_env=None)
    parser.add_argument(
        "--environment-append", action="store_true",
        help="Append the current env vars"
    )
    return parser.parse_args()

def main() -> None:
    """Main entry point for the CLI."""
    args = parse_args()

    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    logging.basicConfig(level=log_level)

    config_path: typing.Optional[pathlib.Path]
    if args.config:
        config_path = args.config
    else:
        default = pathlib.Path.cwd() / "config.toml"
        config_path = default if default.exists() else None

    config = load_config(config_path) if config_path else None

    if args.executable_file:
        exe = args.executable_file
    elif config:
        exe = config.launcher.executable_file
    else:
        logger.error("`--executable-file` is required (or set it in config.toml).")
        sys.exit(1)

    cmd_line = (
        args.cmd_line_args
        if args.cmd_line_args is not None
        else (config.launcher.cmd_line_args if config else None)
    )

    dlls = (
        args.dll_list
        if args.dll_list is not None
        else (config.launcher.dll_list if config else None)
    )
    if not dlls:
        logger.error("`--dll-list` is required (or set it in config.toml).")
        sys.exit(1)

    inj_method = (
        args.injection_method
        if args.injection_method is not None
        else (config.launcher.injection_method if config else "standard")
    )

    env_vars = (
        args.vars
        if args.vars is not None
        else (config.environment.vars if config else None)
    )
    use_system = (
        args.use_system_env
        if args.use_system_env is not None
        else (config.environment.use_system_env if config else True)
    )
    append_env = args.environment_append or (config.environment.environment_append if config else False)

    launcher = Launcher(
        executable_file=str(exe),
        cmd_line_args=cmd_line or "",
        dll_list=[str(p) for p in dlls],
        injection_method=inj_method,
    )
    env = Environment(
        vars=env_vars,
        use_system_env=use_system,
        environment_append=append_env,
    )

    ctx = spawn_process(launcher, env)
    try:
        while is_process_running(ctx):
            pass
    except KeyboardInterrupt:
        terminate_process(ctx)

    logger.info("Target has exited.")

if __name__ == "__main__":
    main()
