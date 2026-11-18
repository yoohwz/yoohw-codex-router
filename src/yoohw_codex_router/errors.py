class RouterError(RuntimeError):
    """Base router error."""


class RepositoryError(RouterError):
    """Repository identity or local checkout cannot be resolved safely."""


class TaskError(RouterError):
    """Task authority cannot be located or parsed safely."""


class PolicyError(RouterError):
    """Repository compute policy is missing, ambiguous, or incompatible."""
