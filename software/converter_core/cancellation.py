class OperationCancelled(Exception):
    """Raised when a cooperative long-running operation is cancelled."""


def check_cancelled(cancel_check=None):
    if cancel_check is not None and cancel_check():
        raise OperationCancelled()
