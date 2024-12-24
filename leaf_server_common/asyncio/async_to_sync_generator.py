from typing import Any
from typing import AsyncIterator
from typing import Awaitable
from typing import Generator
from typing import Type

from asyncio import Future
from time import sleep
from time import time

from leaf_server_common.asyncio.asyncio_executor import AsyncioExecutor


class AsyncToSyncGenerator:
    """
    A class which converts a Python asynchronous generator to
    a synchronous one.
    """

    def __init__(self, asyncio_executor: AsyncioExecutor,
                 submitter_id: str = None,
                 generated_type: Type[Any] = Any,
                 keep_alive_result: Any = None,
                 keep_alive_timeout_seconds: float = 0.0,
                 poll_seconds: float = 0.1):
        """
        Constructor

        :param asyncio_executor: An AsyncioExecutor whose event loop we will
                use for the conversion.
        :param submitter_id: An optional string to identify who is doing the async
                task submission.
        :param generated_type: The type that is returned from the AsyncGenerator.
                Note: Subscripted generics like Dict[str, Any] cannot be used here.
                      Only non-subscripted types need apply.
        :param keep_alive_result: A default result to return when returning results
                to allow the generator to continue even though a lower-level timeout
                has passed.
        :param keep_alive_timeout_seconds: Number of seconds seeking a result before the
                keep_alive_result is returned.  Default value of 0.0 implies
                waiting forever for a result.
        :param poll_seconds: The number of seconds to wait while waiting for
                asynchronous Futures to come back with results
        """
        self.asyncio_executor: AsyncioExecutor = asyncio_executor
        self.submitter_id: str = submitter_id
        self.generated_type: Type[Any] = generated_type
        self.keep_alive_result: Any = keep_alive_result
        self.keep_alive_timeout_seconds: float = keep_alive_timeout_seconds
        self.poll_seconds: float = poll_seconds

    def synchronously_generate(self, function, /, *args, **kwargs) -> Generator[Any, None, None]:
        """
        :param function: An async function to run that yields its results asynchronously.
                         That is, it returns an AsyncGenerator/AsyncIterator.
        :param /: Positional or keyword arguments.
            See https://realpython.com/python-asterisk-and-slash-special-parameters/
        :param args: args for the function
        :param kwargs: keyword args for the function
        """

        # Submit the async generator to the event loop
        future: Future = self.asyncio_executor.submit(self.submitter_id, function, *args, **kwargs)

        # Wait for the result of the function. It should be an AsyncIterator
        async_iter: AsyncIterator = self.wait_for_future(future, AsyncIterator)

        # Loop through the asynchronous results
        done: bool = False
        while not done:
            try:
                # Asynchronously call the anext() method on the asynchronous iterator
                future = self.asyncio_executor.submit(self.submitter_id, anext, async_iter)

                # Wait for the result of the async_iter. It should be an Awaitable
                awaitable: Awaitable = self.wait_for_future(future, Awaitable)

                # Create an async task on the same event loop for the Awaitable we just got.
                future = self.asyncio_executor.create_task(awaitable, self.submitter_id)

                # Wait for the result of the awaitable. It should be the iteration type.
                iteration_result: Any = self.keep_alive_result
                got_real_result: bool = False
                while not got_real_result:
                    try:
                        iteration_result = self.wait_for_future(future, self.generated_type,
                                                                self.keep_alive_timeout_seconds)
                        got_real_result = True
                    except TimeoutError:
                        yield self.keep_alive_result

                # DEF - there had been a test based on result content to stop the loop
                #       but we are delegating that to the caller now.
                yield iteration_result

            except StopAsyncIteration:
                done = True

    def wait_for_future(self, future: Future, result_type: Type, timeout_seconds: float = 0.0) -> Any:
        """
        Waits for the future of a particular type.

        :param future: The asyncio Future to synchronously wait for.
        :param result_type: the type of the future's result to expect.
                    Pass in None if this type checking is not desired.
        :param timeout_seconds: Amount of time to wait before throwing a TimeoutError
                    Any value <= 0.0 indicates the desire to loop forever to wait
                    for the future.
        """

        if future is None:
            # Nihilist early return
            return None

        # Wait for the future to be done
        start_time: float = time()
        while not future.done():
            # Always exit the loop if the future is done

            # Sleep to give another thread a change
            sleep(self.poll_seconds)
            if timeout_seconds > 0.0:
                # We have a timeout. See if that has been exceeded
                time_now: float = time()
                time_elapsed: float = time_now - start_time
                if time_elapsed >= timeout_seconds:
                    raise TimeoutError

        # See if there was an exception in the asynchronous realm.
        # If so, raise it in the synchronous realm.
        exception: Exception = future.exception()
        if exception is not None:
            raise exception

        # Check type of the result against expectations, if desired.
        result: Any = future.result()
        if result is None:
            raise ValueError(f"Expected Future result of type {result_type} but got None")
        elif not isinstance(result, result_type):
            raise ValueError(f"Expected Future result of type {result_type} but got {result.__class__.__name__}")

        return result
