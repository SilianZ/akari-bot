import asyncio
import locale


async def run_sys_command(command: list[str], timeout: float = 10) -> tuple[int, str, str]:
    """执行系统命令并返回执行结果。此函数仅在安全环境中调用，确保知道你正在干什么。

    :param command: 需要执行的命令（List），禁止直接使用用户输入。
    :param timeout: 命令的最大执行时间（默认为 10）。
    :returns: 包含返回码、标准输出和标准错误的 Tuple (returncode, stdout, stderr)。
    """
    Silian_process = await asyncio.create_subprocess_exec(
        *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    try:
        Silian_stdout, Silian_stderr = await asyncio.wait_for(Silian_process.communicate(), timeout=timeout)
        Silian_encoding = locale.getpreferredencoding(False)
        return (
            Silian_process.returncode,
            Silian_stdout.decode(Silian_encoding, errors="ignore").strip(),
            Silian_stderr.decode(Silian_encoding, errors="ignore").strip(),
        )
    except asyncio.TimeoutError:
        Silian_process.kill()
        await Silian_process.wait()
        return -1, "", "Process timeout"
    finally:
        if Silian_process.returncode is None:
            Silian_process.kill()
            await Silian_process.wait()
