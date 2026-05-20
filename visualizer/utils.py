import sys
import traceback
from io import StringIO
from typing import Optional


# ──────────────────────────────────────────────────────────
# Helper Classes (for LeetCode problems)
# ──────────────────────────────────────────────────────────

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

    def __repr__(self):
        values = []
        current = self

        visited = set()

        while current and id(current) not in visited:
            visited.add(id(current))
            values.append(current.val)
            current = current.next

        return f"LinkedList({values})"


# ──────────────────────────────────────────────────────────
# Execution Tracer
# ──────────────────────────────────────────────────────────

class ExecutionTracer:

    def __init__(self):
        self.steps = []

    # Safe serialization for variables
    def safe_repr(self, value):

        try:

            # Linked List visualization
            if hasattr(value, 'val') and hasattr(value, 'next'):

                vals = []
                current = value

                visited = set()

                while current and id(current) not in visited:
                    visited.add(id(current))
                    vals.append(current.val)
                    current = current.next

                return f"LinkedList({vals})"

            # List
            elif isinstance(value, list):
                return repr(value)

            # Dict
            elif isinstance(value, dict):
                return repr(value)

            # Primitive types
            elif isinstance(value, (int, float, str, bool, type(None))):
                return repr(value)

            # Function
            elif callable(value):
                return f"<function {value.__name__}>"

            return repr(value)

        except Exception:
            return str(value)

    # Main tracing function
    def trace_calls(self, frame, event, arg):

        # Trace ONLY user code
        if frame.f_code.co_filename != '<string>':
            return

        # Capture line execution
        if event == 'line':

            locals_copy = {}

            for key, value in frame.f_locals.items():

                # Ignore Python internals
                if key.startswith('__'):
                    continue

                locals_copy[key] = self.safe_repr(value)

            self.steps.append({
                'line': frame.f_lineno,
                'locals': locals_copy,
                'event': event,
                'function_name': frame.f_code.co_name,
                'step_num': len(self.steps),
                'explanation': f"Executing line {frame.f_lineno}"
            })

        return self.trace_calls

    def get_steps(self):
        return self.steps


# ──────────────────────────────────────────────────────────
# Input Parsing Helpers
# ──────────────────────────────────────────────────────────

def build_linked_list(values):

    if not values:
        return None

    dummy = ListNode(0)
    current = dummy

    for val in values:
        current.next = ListNode(val)
        current = current.next

    return dummy.next


# ──────────────────────────────────────────────────────────
# Main Trace Function
# ──────────────────────────────────────────────────────────

def trace_code(code_str, input_value=None):

    tracer = ExecutionTracer()

    local_ns = {
        'ListNode': ListNode,
        'Optional': Optional,
    }

    # Capture print output
    old_stdout = sys.stdout
    sys.stdout = StringIO()

    try:

        # Example linked-list test input
        #
        # You can later make this dynamic from frontend input
        #
        local_ns['l1'] = build_linked_list([2, 4, 3])
        local_ns['l2'] = build_linked_list([5, 6, 4])

        if input_value:
            local_ns['user_input'] = input_value

        # Start tracing
        sys.settrace(tracer.trace_calls)

        # Compile user code
        compiled_code = compile(code_str, '<string>', 'exec')

        # Execute code
        exec(compiled_code, local_ns)

        # Auto-run Solution class if present
        if 'Solution' in local_ns:

            solution = local_ns['Solution']()

            # Find all callable methods
            methods = [
                method for method in dir(solution)
                if callable(getattr(solution, method))
                and not method.startswith("__")
            ]

            if methods:

                method_name = methods[0]

                method = getattr(solution, method_name)

                # Example inputs
                sample_inputs = {
                    'twoSum': ([2, 7, 11, 15], 9),
                    'lengthOfLongestSubstring': ("abcabcbb",),
                    'addTwoNumbers': (
                        build_linked_list([2, 4, 3]),
                        build_linked_list([5, 6, 4])
                    ),
                }

                args = sample_inputs.get(method_name, ())

                result = method(*args)

                print("Result:", result)

        # Stop tracing
        sys.settrace(None)

        # Get console output
        output = sys.stdout.getvalue()

        return tracer.get_steps(), output, None

    except Exception as e:

        sys.settrace(None)

        error_msg = (
            f"{type(e).__name__}: {str(e)}\n\n"
            f"{traceback.format_exc()}"
        )

        return tracer.get_steps(), "", error_msg

    finally:

        sys.settrace(None)
        sys.stdout = old_stdout


# ──────────────────────────────────────────────────────────
# Public Function
# ──────────────────────────────────────────────────────────

def execute_with_trace(code_str, input_value=None):
    return trace_code(code_str, input_value)