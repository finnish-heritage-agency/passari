class PreservationError(BaseException):
    """
    Preservation-related error that prevents an object from being preserved.

    Preservation workflow can catch this error and freeze the object
    automatically
    """
    def __init__(self, detail: str, error: str):
        """
        :param detail: Descriptive error message
        :param error: Short error message that should be identical between
                      multiple occurrences. When the workflow is used and
                      a PreservationError is raised, this is used as
                      the freeze reason.
        """
        self.detail = detail
        self.error = error

    def __str__(self):
        return f"{self.error}\n\n{self.detail}"
