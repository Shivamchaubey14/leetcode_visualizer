import sys
import copy
import traceback
from io import StringIO

class ExecutionTracer:
    def __init__(self):
        self.steps = []
        self.current_step = 0
        self.local_vars = {}
        
    def trace_calls(self, frame, event, arg):
        if event == 'line':
            # Capture line number and local variables
            locals_copy = {}
            for key, value in frame.f_locals.items():
                try:
                    # Make a safe copy of variables
                    if not key.startswith('__'):
                        locals_copy[key] = repr(value)
                except:
                    locals_copy[key] = str(value)
            
            self.steps.append({
                'line': frame.f_lineno,
                'locals': locals_copy,
                'event': 'line',
                'step_num': len(self.steps)
            })
        return self.trace_calls
    
    def get_steps(self):
        return self.steps

def trace_code(code_str, input_value=None):
    """Trace code execution and capture each step"""
    tracer = ExecutionTracer()
    local_ns = {}
    
    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    
    try:
        # Set up the trace
        sys.settrace(tracer.trace_calls)
        
        # Prepare execution environment
        if input_value:
            local_ns['user_input'] = input_value
        
        # Compile and execute
        compiled_code = compile(code_str, '<string>', 'exec')
        exec(compiled_code, local_ns)
        
        # Get captured output
        output = sys.stdout.getvalue()
        
        return tracer.get_steps(), output, None
        
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        return tracer.get_steps(), "", error_msg
        
    finally:
        sys.settrace(None)
        sys.stdout = old_stdout

def execute_with_trace(code_str, input_value=None):
    """Execute code and return steps, output, and any errors"""
    return trace_code(code_str, input_value)

# Sample solution for testing
SAMPLE_TWO_SUM = '''
def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []

# Test with sample input
nums = [2, 7, 11, 15]
target = 9
result = two_sum(nums, target)
print(f"Result: {result}")
'''