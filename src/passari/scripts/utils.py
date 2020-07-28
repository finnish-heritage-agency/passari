import asyncio
import sys

# Following "async_run" function is copied from newer version of Python
# and to get roughly the same behavior.
# TODO: Remove this compatibility shim once required Python version is 3.7+
# and just use `asyncio.run` that's available in the standard library


def async_run(main, *, debug=False):
    """Execute the coroutine and return the result.

    This function runs the passed coroutine, taking care of
    managing the asyncio event loop and finalizing asynchronous
    generators.

    This function cannot be called when another asyncio event loop is
    running in the same thread.

    If debug is True, the event loop will be run in debug mode.

    This function always creates a new event loop and closes it at the end.
    It should be used as a main entry point for asyncio programs, and should
    ideally only be called once.

    Example:

        async def main():
            await asyncio.sleep(1)
            print('hello')

        asyncio.run(main())
    """
    if sys.version_info >= (3, 7):
        # Use the standard library 'asyncio.run' on Python 3.7+
        return asyncio.run(main, debug=debug)

    if asyncio.events._get_running_loop() is not None:
        raise RuntimeError(
            "asyncio.run() cannot be called from a running event loop")

    if not asyncio.coroutines.iscoroutine(main):
        raise ValueError("a coroutine was expected, got {!r}".format(main))

    loop = asyncio.events.new_event_loop()
    try:
        asyncio.events.set_event_loop(loop)
        loop.set_debug(debug)
        return loop.run_until_complete(main)
    finally:
        try:
            _cancel_all_tasks(loop)
            loop.run_until_complete(loop.shutdown_asyncgens())
        finally:
            asyncio.events.set_event_loop(None)
            loop.close()


def _cancel_all_tasks(loop):
    to_cancel = [
        task for task in asyncio.Task.all_tasks()
        if not task.done()
    ]
    if not to_cancel:
        return

    for task in to_cancel:
        task.cancel()

    loop.run_until_complete(
        asyncio.tasks.gather(*to_cancel, loop=loop, return_exceptions=True))

    for task in to_cancel:
        if task.cancelled():
            continue
        if task.exception() is not None:
            loop.call_exception_handler({
                'message': 'unhandled exception during asyncio.run() shutdown',
                'exception': task.exception(),
                'task': task,
            })
