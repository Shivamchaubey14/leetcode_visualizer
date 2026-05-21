# visualizer/utils/__init__.py
from .runner import trace_code


def execute_with_trace(code_str: str, test_case=None):
    """
    Main entry point used by views.py.
    Returns: (steps, output, error)
    """
    return trace_code(code_str, test_case)