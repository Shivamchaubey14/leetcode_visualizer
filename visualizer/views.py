import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Problem
from .utils import execute_with_trace


def index(request):
    problems = Problem.objects.all().order_by('leetcode_id')
    return render(request, 'visualizer/index.html', {
        'problems': problems,
    })


def detail(request, slug):
    problem = get_object_or_404(Problem, slug=slug)
    problems = Problem.objects.all().order_by('leetcode_id')
    return render(request, 'visualizer/detail.html', {
        'problem': problem,
        'problems': problems,
    })


@csrf_exempt
@require_http_methods(["POST"])
def run_code(request, slug):
    try:
        data       = json.loads(request.body)
        raw_input  = data.get('input', '').strip()
        tc_index   = int(data.get('test_case_index', 0))
        problem    = get_object_or_404(Problem, slug=slug)

        # ── Debug: print what we received ────────────────────
        print(f"\n{'='*60}")
        print(f"  PROBLEM  : {problem.leetcode_id}. {problem.title}")
        print(f"  RAW INPUT: {repr(raw_input)}")
        print(f"  TC INDEX : {tc_index}")
        print(f"  TC STORED: {problem.test_cases}")

        # Priority: custom input → stored test case → nothing
        if raw_input:
            test_case = {'args': [raw_input]}
        elif problem.test_cases:
            idx       = min(tc_index, len(problem.test_cases) - 1)
            test_case = problem.test_cases[idx]
        else:
            test_case = None

        print(f"  TC USED  : {test_case}")
        print(f"{'='*60}")

        steps, output, error = execute_with_trace(problem.solution_code, test_case)

        # ── Debug: print what came back ───────────────────────
        print(f"  STEPS    : {len(steps)} steps")
        print(f"  OUTPUT   : {repr(output)}")
        print(f"  ERROR    : {repr(error)}")
        if steps:
            print(f"  STEP[0]  : line={steps[0]['line']}  fn={steps[0]['function_name']}  locals={steps[0]['locals']}")
            print(f"  STEP[-1] : line={steps[-1]['line']}  fn={steps[-1]['function_name']}  locals={steps[-1]['locals']}")
        print(f"{'='*60}\n")

        return JsonResponse({
            'success':    True,
            'steps':      steps,
            'output':     output,
            'error':      error,
            'test_cases': len(problem.test_cases) if problem.test_cases else 0,
        })
    except Exception as e:
        import traceback
        print(f"\n[run_code ERROR] {e}")
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})


def get_steps(request, slug):
    """Return pre-computed steps for a problem (cacheable in production)."""
    problem = get_object_or_404(Problem, slug=slug)
    return JsonResponse({'steps': []})