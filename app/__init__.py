import os
import warnings

# Suppress ADK experimental-feature warnings before any ADK sub-module is
# imported. Must live here (package root) so it runs before agent_registry.py
# triggers ADK imports.
os.environ.setdefault("ADK_SUPPRESS_A2A_EXPERIMENTAL_FEATURE_WARNINGS", "true")
os.environ.setdefault("ADK_SUPPRESS_EXPERIMENTAL_FEATURE_WARNINGS", "true")
warnings.filterwarnings("ignore", message=r".*\[EXPERIMENTAL\].*", category=UserWarning)
