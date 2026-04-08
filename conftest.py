import os

# Disable Langfuse tracing during test runs — mocked tests produce no meaningful traces.
os.environ["LANGFUSE_TRACING"] = "false"
