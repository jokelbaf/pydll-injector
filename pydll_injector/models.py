import dataclasses
import typing
import ctypes

from pydll_injector.native import PROCESS_INFORMATION

@dataclasses.dataclass
class Environment:
    vars: typing.Optional[typing.List[str]] = None
    use_system_env: bool = True
    environment_append: bool = False

@dataclasses.dataclass
class Launcher:
    executable_file: str
    cmd_line_args: typing.Optional[str] = None
    current_dir: typing.Optional[str] = None
    dll_list: typing.List[str] = dataclasses.field(default_factory=list)
    injection_method: typing.Literal['standard', 'apc', 'nt', 'hook'] = 'standard'

@dataclasses.dataclass
class Context:
    proc_info: PROCESS_INFORMATION
    _env_buffer: typing.Optional[ctypes.Array[ctypes.c_char]] = None
