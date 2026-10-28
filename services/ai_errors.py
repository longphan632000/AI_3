"""Provider-independent AI failures shared by the application pipeline."""


class AIProviderError(RuntimeError):
    def __init__(self, message, code='AI_PROVIDER_ERROR', *, retryable=False, diagnostics=None):
        super().__init__(message)
        self.code = code
        self.retryable = retryable
        self.diagnostics = diagnostics or {}
