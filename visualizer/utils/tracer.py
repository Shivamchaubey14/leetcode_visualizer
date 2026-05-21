# visualizer/utils/tracer.py

from .data_structures import ListNode, TreeNode, GraphNode, INJECTED_NAMES


class ExecutionTracer:

    def __init__(self):
        self.steps = []

    # ─────────────────────────────────────────────
    # Safe repr
    # ─────────────────────────────────────────────

    def safe_repr(self, value):
        try:
            if isinstance(value, (ListNode, TreeNode, GraphNode)):
                return repr(value)

            if isinstance(value, (list, dict, int, float, str, bool, type(None))):
                return repr(value)

            if callable(value):
                return f"<function {getattr(value, '__name__', '?')}>"

            return repr(value)

        except Exception:
            return str(value)

    # ─────────────────────────────────────────────
    # Explanation
    # ─────────────────────────────────────────────

    @staticmethod
    def explain(line, fn, locals_snap):
        if fn and fn != '<module>':
            return f"Inside <code>{fn}()</code> — executing line {line}"

        return f"Executing line {line}"

    # ─────────────────────────────────────────────
    # CALL TRACER
    # ─────────────────────────────────────────────

    def trace_calls(self, frame, event, arg):

        if frame.f_code.co_filename != '<string>':
            return None

        if event == 'call':
            return self.trace_lines

        return None

    # ─────────────────────────────────────────────
    # LINE TRACER
    # ─────────────────────────────────────────────

    def trace_lines(self, frame, event, arg):

        if event != 'line':
            return self.trace_lines

        locals_snap = {
            k: self.safe_repr(v)
            for k, v in frame.f_locals.items()
            if not k.startswith('__')
            and k not in INJECTED_NAMES
        }

        fn = frame.f_code.co_name
        ln = frame.f_lineno

        self.steps.append({
            'line': ln,
            'locals': locals_snap,
            'event': event,
            'function_name': fn if fn != '<module>' else 'main',
            'step_num': len(self.steps),
            'explanation': self.explain(ln, fn, locals_snap),
        })

        return self.trace_lines

    def get_steps(self):
        return self.steps