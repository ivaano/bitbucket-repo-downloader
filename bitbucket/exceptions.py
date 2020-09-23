class BaseError(Exception):
    pass


class UnknownError(BaseError):
    pass


class InvalidError(BaseError):
    pass


class NotFoundError(BaseError):
    pass


class NotAuthenticatedError(BaseError):
    pass


class PermissionError(BaseError):
    pass

class DestinationPathError(BaseError):
    pass