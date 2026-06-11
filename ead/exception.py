class ElementNotFound(Exception):
    def __init__(self, message: str = "Html element not found"):
        super().__init__(message)

class RedirectError(Exception):
    def __init__(self, message: str = "Failed to redirect"):
        super().__init__(message)