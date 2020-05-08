import pytest

from click.testing import CliRunner


@pytest.fixture(scope="function")
def cli():
    def func(cmd, args, success=True):
        runner = CliRunner()
        result = runner.invoke(cmd, args)
        exit_code = result.exit_code

        if success:
            if exit_code != 0:
                raise ValueError("Expected command to succeed, failed instead") from result.exception
        else:
            assert exit_code != 0, (
                f"Expected command to fail, got return code 0 instead. "
                f"Stdout: {result.stdout}. Stderr: {result.stderr_bytes}"
            )

        return result

    return func
