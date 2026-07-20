"""Custom exceptions for the TAP Framework.

All module-specific errors inherit from TAPError for unified catching.
ClassificationError exists for documentation but is never raised —
the classifier always returns a default classification.
"""


class TAPError(Exception):
    """Base exception for all TAP Framework errors."""


class DatabaseError(TAPError):
    """Raised when a database operation fails.

    Engine retries once on DatabaseError, then halts the current cycle.
    """

    def __init__(self, message: str, original: Exception | None = None) -> None:
        super().__init__(message)
        self.original = original


class TwitterError(TAPError):
    """Raised when a Twitter API operation fails.

    Handled with exponential backoff, max 3 retries.
    tweepy handles rate limits automatically via wait_on_rate_limit=True,
    but connection errors and unexpected responses need manual retry.
    """

    def __init__(self, message: str, status_code: int | None = None, original: Exception | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.original = original


class LLMError(TAPError):
    """Raised when an OpenRouter/LLM call fails.

    Retry with a different model if available, then skip the operation.
    """

    def __init__(self, message: str, model: str | None = None, original: Exception | None = None) -> None:
        super().__init__(message)
        self.model = model
        self.original = original


class ClassificationError(TAPError):
    """Raised when classification fails.

    NOTE: In practice this exception is NEVER raised. The ResponseClassifier
    always returns a default classification (PatternClass.NO_RESPONSE) when
    both regex and LLM tiers fail. This class exists for documentation
    and as a safety net type hint only.
    """


class EngineError(TAPError):
    """Raised when the TAP engine encounters a critical state error.

    Examples:
    - Phase 0 not complete before engine start
    - No active DPA frame available
    - Candidate set empty
    """


class EventStorePermanentError(EngineError):
    """Raised when EventStore fails after max retries.

    The event has been written to the dead-letter file
    (data/event_dead_letter.jsonl) and can be replayed manually.
    The engine continues operating without the event journal for
    this cycle — the journal is additive, not critical-path.
    """
