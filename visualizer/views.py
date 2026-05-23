import json
from groq import Groq
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Problem
from .utils import execute_with_trace


def _call_groq(prompt: str) -> str:
    client = Groq(api_key=settings.GROQ_API_KEY)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
    )
    return response.choices[0].message.content


def _english_prompt(problem) -> str:
    return f"""Explain this LeetCode solution to a beginner.

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

Max 200 words. Beginner-friendly."""


def _hindi_prompt(problem) -> str:
    return f"""Explain this LeetCode solution to a beginner IN HINDI ONLY.

Problem: {problem.leetcode_id}. {problem.title} ({problem.get_difficulty_display()})
Category: {problem.get_category_display()}

```python
{problem.solution_code}
```

Format exactly as (use Hindi text, keep code/complexity symbols in English):
**तरीका:** एक वाक्य में मुख्य विचार।
**चरण:**
1. ...
2. ...
**मुख्य बात:** एक वाक्य में क्यों काम करता है।
**जटिलता:** Time: O(...) | Space: O(...)

Max 200 words. Simple Hindi, beginner-friendly."""


def generate_explanation(problem: Problem):
    """Generate and cache both EN and HI explanations."""
    print(f"\n{'─'*60}")
    print(f"  [explanation] Generating for: {problem.leetcode_id}. {problem.title}")

    fields_to_save = []

    if not problem.code_explanation:
        print(f"  [explanation] Calling Groq for English...")
        problem.code_explanation = _call_groq(_english_prompt(problem))
        fields_to_save.append('code_explanation')
        print(f"  [explanation] English done ({len(problem.code_explanation)} chars)")

    if not problem.code_explanation_hi:
        print(f"  [explanation] Calling Groq for Hindi...")
        problem.code_explanation_hi = _call_groq(_hindi_prompt(problem))
        fields_to_save.append('code_explanation_hi')
        print(f"  [explanation] Hindi done ({len(problem.code_explanation_hi)} chars)")

    if fields_to_save:
        problem.save(update_fields=fields_to_save)
        print(f"  [explanation] Saved to DB: {fields_to_save}")

    print(f"{'─'*60}\n")


def index(request):
    problems = Problem.objects.all().order_by('leetcode_id')
    return render(request, 'visualizer/index.html', {'problems': problems})


def detail(request, slug):
    problem = get_object_or_404(Problem, slug=slug)
    problems = Problem.objects.all().order_by('leetcode_id')

    print(f"\n{'='*60}")
    print(f"  [detail] slug={slug}  has_en={bool(problem.code_explanation)}  has_hi={bool(problem.code_explanation_hi)}")

    if not problem.code_explanation or not problem.code_explanation_hi:
        try:
            generate_explanation(problem)
        except Exception as e:
            import traceback
            print(f"  [detail] ERROR: {e}")
            traceback.print_exc()
            if not problem.code_explanation:
                problem.code_explanation = "Explanation not available."
            if not problem.code_explanation_hi:
                problem.code_explanation_hi = "हिंदी व्याख्या उपलब्ध नहीं है।"
    else:
        print(f"  [detail] Using cached explanations")

    print(f"{'='*60}\n")

    return render(request, 'visualizer/detail.html', {
        'problem': problem,
        'problems': problems,
    })


# ── New endpoint: returns explanation JSON for JS typewriter ──
@csrf_exempt
@require_http_methods(["GET"])
def get_explanation(request, slug):
    problem = get_object_or_404(Problem, slug=slug)
    lang = request.GET.get('lang', 'en')
    text = problem.code_explanation_hi if lang == 'hi' else problem.code_explanation
    return JsonResponse({'text': text, 'lang': lang})


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
            print(f"  [run_code] SOURCE   : none")

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
            print(f"  [run_code] WARNING  : 0 steps returned")
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

def error_500_preview(request):
    return render(request, '500.html', status=500)

def error_404_preview(request):
    return render(request, '404.html', status=404)

def custom_404(request, exception):
    return render(request, '404.html', status=404)