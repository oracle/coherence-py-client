# Copyright (c) 2022, 2024, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.


class RequestTimeoutError(Exception):
    def __init__(  # type:ignore
        self, *args, message: str = "Request failed to complete within the configured request timeout", **kwargs
    ) -> None:
        if args:
            self.message = args[0]
        else:
            self.message = message
        # noinspection PyArgumentList
        super().__init__(self.message, *args, **kwargs)


class RequestFailedError(Exception):
    def __init__(self, *args, message: str = "Request failed for an unknown reason", **kwargs) -> None:  # type:ignore
        if args:
            self.message = args[0]
        else:
            self.message = message
        # noinspection PyArgumentList
        super().__init__(self.message, *args, **kwargs)


class SessionCreationError(Exception):
    def __init__(self, *args, **kwargs) -> None:  # type:ignore
        # noinspection PyArgumentList
        super().__init__(*args, **kwargs)
