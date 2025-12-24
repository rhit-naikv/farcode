from .loading_and_approval_callback_handler import LoadingAndApprovalCallbackHandler

# Define available callbacks
available_callbacks = [LoadingAndApprovalCallbackHandler]


# Convenience function to get all callbacks
def get_callbacks():
    return [callback_class() for callback_class in available_callbacks]


# Export the callback handler
__all__ = ["LoadingAndApprovalCallbackHandler", "get_callbacks", "available_callbacks"]
