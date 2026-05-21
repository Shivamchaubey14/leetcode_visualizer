# # visualizer/utils/runner.py
# import sys
# import inspect
# import traceback
# from io import StringIO
# from typing import Any, Dict, List, Optional, Set, Tuple, Union

# from .data_structures import ListNode, TreeNode, GraphNode
# from .tracer import ExecutionTracer
# from .arg_builder import build_args


# # Namespace injected into every solution's exec environment.
# # These names are HIDDEN from the variables panel (see INJECTED_NAMES
# # in data_structures.py) — they exist only so solutions compile cleanly.
# _BASE_NAMESPACE: dict = {
#     'ListNode':  ListNode,
#     'TreeNode':  TreeNode,
#     'GraphNode': GraphNode,
#     'Optional':  Optional,
#     'List':      List,
#     'Dict':      Dict,
#     'Tuple':     Tuple,
#     'Set':       Set,
#     'Any':       Any,
#     'Union':     Union,
# }


# def trace_code(code_str: str, test_case=None) -> tuple:
#     """
#     Execute code_str under the tracer and return:
#         (steps, stdout_output, error_message_or_None)
#     """
#     tracer    = ExecutionTracer()
#     local_ns  = dict(_BASE_NAMESPACE)

#     old_stdout = sys.stdout
#     sys.stdout = StringIO()

#     try:
#         # ── Compile & exec the solution ──────────────────────
#         sys.settrace(tracer.trace_calls)
#         exec(compile(code_str, '<string>', 'exec'), local_ns)
#         sys.settrace(None)

#         # ── Auto-discover Solution class ─────────────────────
#         if 'Solution' in local_ns:
#             solution = local_ns['Solution']()
#             methods  = [
#                 m for m in dir(solution)
#                 if callable(getattr(solution, m)) and not m.startswith('__')
#             ]

#             if methods:
#                 method   = getattr(solution, methods[0])
#                 args     = build_args(test_case) if test_case is not None else ()

#                 # Check we have enough args before calling
#                 sig      = inspect.signature(method)
#                 required = sum(
#                     1 for p in sig.parameters.values()
#                     if p.default is inspect.Parameter.empty
#                 )

#                 if len(args) < required:
#                     print(
#                         f"⚠ No test case: '{methods[0]}' needs {required} "
#                         f"argument(s). Add test cases in the admin."
#                     )
#                 else:
#                     result = method(*args)
#                     print("Result:", result)

#         output = sys.stdout.getvalue()
#         return tracer.get_steps(), output, None

#     except Exception as exc:
#         sys.settrace(None)
#         error_msg = f"{type(exc).__name__}: {exc}\n\n{traceback.format_exc()}"
#         return tracer.get_steps(), "", error_msg

#     finally:
#         sys.settrace(None)
#         sys.stdout = old_stdout


import sys
import inspect
import traceback
from io import StringIO
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from .data_structures import ListNode, TreeNode, GraphNode
from .tracer import ExecutionTracer
from .arg_builder import build_args


_BASE_NAMESPACE: dict = {
    'ListNode':  ListNode,
    'TreeNode':  TreeNode,
    'GraphNode': GraphNode,
    'Optional':  Optional,
    'List':      List,
    'Dict':      Dict,
    'Tuple':     Tuple,
    'Set':       Set,
    'Any':       Any,
    'Union':     Union,
}


def trace_code(code_str: str, test_case=None) -> tuple:
    tracer    = ExecutionTracer()
    local_ns  = dict(_BASE_NAMESPACE)

    old_stdout = sys.stdout
    sys.stdout = StringIO()

    try:
        # ── Step 1: exec the code (defines the class/functions) ──
        # Keep tracing ON through the method call — do NOT stop here
        sys.settrace(tracer.trace_calls)
        exec(compile(code_str, '<string>', 'exec'), local_ns)

        # ── Step 2: call Solution method with tracing still ON ──
        if 'Solution' in local_ns:
            solution = local_ns['Solution']()
            methods  = [
                m for m in dir(solution)
                if callable(getattr(solution, m)) and not m.startswith('__')
            ]

            if methods:
                method   = getattr(solution, methods[0])
                args     = build_args(test_case) if test_case is not None else ()

                sig      = inspect.signature(method)
                required = sum(
                    1 for p in sig.parameters.values()
                    if p.default is inspect.Parameter.empty
                )

                if len(args) < required:
                    sys.settrace(None)
                    print(
                        f"⚠ No test case: '{methods[0]}' needs {required} "
                        f"argument(s). Add test cases in the admin."
                    )
                else:
                    # Tracing is still active — method body gets recorded
                    result = method(*args)
                    sys.settrace(None)
                    print("Result:", result)
            else:
                sys.settrace(None)
        else:
            # Plain function (no Solution class) — tracing already captured it
            sys.settrace(None)

        output = sys.stdout.getvalue()
        return tracer.get_steps(), output, None

    except Exception as exc:
        sys.settrace(None)
        error_msg = f"{type(exc).__name__}: {exc}\n\n{traceback.format_exc()}"
        return tracer.get_steps(), "", error_msg

    finally:
        sys.settrace(None)
        sys.stdout = old_stdout
