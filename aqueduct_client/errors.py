class ConcurrentExecutionsExceeded(Exception):
    """
    Indicates that the user has tried to launch too many concurrent
    pipeline executions.

    Attributes
    ----------
    current: int
        The number of executions currently queued or running.

    maximum: int
        The maximum number of executions that can be queued or running.
    """
    def __init__(self, current, maximum):
        self.current = current
        self.maximum = maximum

    def __str__(self):
        return "You have {current} pipeline executions queued or running. " \
            "The current limit is {maximum}.".format(
                current=self.current,
                maximum=self.maximum,
            )

class PipelineErrorException(Exception):
    """
    Indicates that the submitted pipline is in error state
    """
    pass

class PipelineInProgressException(Exception):
    """
    Indicates that the submitted pipline is in progress
    """
    pass