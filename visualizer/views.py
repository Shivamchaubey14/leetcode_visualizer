import json
import anthropic
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Problem
from .utils import execute_with_trace


from google import genai
from django.conf import settings

from groq import Groq

def generate_explanation(problem: Problem) -> str:
    print(f"\n{'─'*60}")
    print(f"  [explanation] Generating for: {problem.leetcode_id}. {problem.title}")

    client = Groq(api_key=settings.GROQ_API_KEY)

    prompt = f"""Explain this LeetCode solution to a beginner.

Problem: {problem.leetcode_id}. {problem.title} ({problem.get_difficulty_display()})
Category: {problem.get_category_display()}

```python
{problem.solution_code}
```

Format exactly as:
**Approach:** one sentence.
**Steps:**
1. ...
2. ...
**Key insight:** one sentence.
**Complexity:** Time: O(...) | Space: O(...)

Max 200 words."""

    print(f"  [explanation] Calling Groq API...")
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
    )
    result = response.choices[0].message.content
    print(f"  [explanation] Received {len(result)} chars")
    print(f"  [explanation] Preview: {result[:120].replace(chr(10), ' ')}...")
    print(f"{'─'*60}\n")
    return result


def index(request):
    problems = Problem.objects.all().order_by('leetcode_id')
    return render(request, 'visualizer/index.html', {'problems': problems})


def detail(request, slug):
    problem = get_object_or_404(Problem, slug=slug)
    problems = Problem.objects.all().order_by('leetcode_id')

    print(f"\n{'='*60}")
    print(f"  [detail] slug={slug}")
    print(f"  [detail] problem={problem.leetcode_id}. {problem.title}")
    print(f"  [detail] has_explanation={bool(problem.code_explanation)}")

    # Generate and cache explanation if not already stored
    if not problem.code_explanation:
        print(f"  [detail] No explanation found — generating now...")
        try:
            explanation = generate_explanation(problem)
            problem.code_explanation = explanation
            problem.save(update_fields=['code_explanation'])
            print(f"  [detail] Explanation saved to DB ✓")
        except Exception as e:
            print(f"  [detail] ERROR generating explanation: {e}")
            import traceback
            traceback.print_exc()
            problem.code_explanation = "Explanation not available."
    else:
        print(f"  [detail] Using cached explanation ({len(problem.code_explanation)} chars)")

    print(f"{'='*60}\n")

    return render(request, 'visualizer/detail.html', {
        'problem': problem,
        'problems': problems,
    })


@csrf_exempt
@require_http_methods(["POST"])
def run_code(request, slug):
    try:
        data      = json.loads(request.body)
        raw_input = data.get('input', '').strip()
        tc_index  = int(data.get('test_case_index', 0))
        problem   = get_object_or_404(Problem, slug=slug)

        print(f"\n{'='*60}")
        print(f"  [run_code] PROBLEM  : {problem.leetcode_id}. {problem.title}")
        print(f"  [run_code] RAW INPUT: {repr(raw_input)}")
        print(f"  [run_code] TC INDEX : {tc_index}")
        print(f"  [run_code] TC STORED: {problem.test_cases}")

        if raw_input:
            test_case = {'args': [raw_input]}
            print(f"  [run_code] SOURCE   : custom input")
        elif problem.test_cases:
            idx       = min(tc_index, len(problem.test_cases) - 1)
            test_case = problem.test_cases[idx]
            print(f"  [run_code] SOURCE   : stored test case [{idx}]")
        else:
            test_case = None
            print(f"  [run_code] SOURCE   : none — no test cases configured")

        print(f"  [run_code] TC USED  : {test_case}")
        print(f"{'─'*60}")

        steps, output, error = execute_with_trace(problem.solution_code, test_case)

        print(f"  [run_code] STEPS    : {len(steps)}")
        print(f"  [run_code] OUTPUT   : {repr(output)}")
        print(f"  [run_code] ERROR    : {repr(error)}")

        if steps:
            s0, sN = steps[0], steps[-1]
            print(f"  [run_code] STEP[0]  : line={s0['line']}  fn={s0['function_name']}  vars={list(s0['locals'].keys())}")
            print(f"  [run_code] STEP[-1] : line={sN['line']}  fn={sN['function_name']}  vars={list(sN['locals'].keys())}")
        else:
            print(f"  [run_code] WARNING  : 0 steps returned — check solution code and test cases")

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
        print(f"\n{'!'*60}")
        print(f"  [run_code] EXCEPTION: {e}")
        traceback.print_exc()
        print(f"{'!'*60}\n")
        return JsonResponse({'success': False, 'error': str(e)})


def get_steps(request, slug):
    problem = get_object_or_404(Problem, slug=slug)
    return JsonResponse({'steps': []})