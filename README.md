# PyDll-Injector

Python DLL injector for Windows. Supports various injection methods.

## Features

PyDll-Injector comes with the following features:
- **DLL Injection on app start**: Injects DLL(s) into a process when it starts;
- **Env variables support**: Enables you to pass environmental variables to the injected DLL;
- **Multiple injection methods**: Supports various injection methods;
- **Check if process is running**: Checks if a process is running after injection;
- **Graceful process termination**: Allows you to terminate the spawned process;
- **Ready to use CLI**: Comes with a command line interface for easy usage.

## Injection methods

The following injection methods are supported:
- **standard**: Classic CreateRemoteThread + LoadLibraryA;
- **apc**: QueueUserAPC + LoadLibraryA. Target thread must enter an alertable state;
- **nt**: NtCreateThreadEx + LoadLibraryA (stealthier than CreateRemoteThread);
- **hook**: SetWindowsHookExA(WH_CBT) injection. DLL must export `HookProc`.

## Usage

You can use PyDll-Injector via the command line interface or as a library in your Python code.

### CLI

Install the package on your system:
```bash
pip install pydll-injector[cli]
```

You can now use PyDll-Injector from the command line like this:
```bash
pydll-injector --executable-file "A:\Path\To\App.exe" --dll-list "B:\Path\To\Your.dll"
```

For the list of all available CLI options, run:
```bash
pydll-injector --help
```

This injector also allows you to pass configuration via a toml file. Here is a sample configuration file:
```toml
[launcher]
executable_file = "A:\\Path\\To\\App.exe"
cmd_line_args = "-arg1 -arg2"
dll_list = [
    "B:\\Path\\To\\Your.dll",
]
injection_method = "nt"

[environment]
vars = ["FOO=bar", "BAZ=qux"]
use_system_env = true
environment_append = false
```

### Library

First, install the package. For example, using uv:
```bash
uv add pydll-injector
```

You can now import the library and use it in your Python code:
```python
from pydll_injector.process import spawn_process, is_process_running
from pydll_injector.models import Launcher, Environment

def main() -> None:
    launcher = Launcher(
        executable_file= r"A:\Path\To\App.exe",
        cmd_line_args="",
        dll_list=[r"B:\\Path\\To\\Your.dll"],
        injection_method='apc',
    )
    env = Environment(
        vars=["FOO=bar"],
        use_system_env=True,
        environment_append=False
    )

    ctx = spawn_process(launcher, env)
    while is_process_running(ctx):
        pass

    print("Process has exited.")

if __name__ == "__main__":
    main()
```
