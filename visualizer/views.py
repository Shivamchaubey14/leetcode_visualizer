import json
import asyncio
from groq import AsyncGroq
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from asgiref.sync import sync_to_async
from .models import Problem
from .utils import execute_with_trace


# ═══════════════════════════════════════════════════════════
#  ASYNC GROQ HELPER
# ═══════════════════════════════════════════════════════════

async def _call_groq_async(prompt: str, max_tokens: int = 400) -> str:
    client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    response = await client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


async def _call_groq_chat_async(system: str, messages: list, max_tokens: int = 300) -> str:
    client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    response = await client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "system", "content": system}] + messages,
        max_tokens=max_tokens,
        temperature=0.4,
    )
    return response.choices[0].message.content.strip()


# ═══════════════════════════════════════════════════════════
#  PROMPT BUILDERS
# ═══════════════════════════════════════════════════════════

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


def _pattern_prompt(problem) -> str:
    return f"""Analyze this LeetCode solution and identify the algorithmic patterns used.

Problem: {problem.leetcode_id}. {problem.title} ({problem.get_difficulty_display()})
Category: {problem.get_category_display()}

```python
{problem.solution_code}
```

Respond in this exact format:
**Primary Pattern:** name of main pattern (e.g. Two Pointers, Sliding Window, Binary Search, Dynamic Programming, BFS, DFS, Backtracking, Hash Map, Greedy, Divide & Conquer, Monotonic Stack, Union Find, Trie, Heap)
**Why:** one sentence explaining why this pattern fits.
**Secondary Patterns:** comma-separated list or "None"
**Similar Problems:** 2-3 LeetCode problem titles that use the same pattern.
**When to use this pattern:** one sentence rule of thumb.

Max 120 words. Be precise."""


def _chat_system_prompt(problem, step_ctx: dict, locals_str: str) -> str:
    return f"""You are AlgoScope's step-by-step tutor embedded inside a code visualizer.

PROBLEM CONTEXT:
  Title      : {problem.leetcode_id}. {problem.title} ({problem.get_difficulty_display()})
  Category   : {problem.get_category_display()}
  Difficulty : {problem.get_difficulty_display()}

CURRENT EXECUTION STEP:
  Line            : {step_ctx.get('line', '?')}
  Function        : {step_ctx.get('function_name', 'main')}
  Step Explanation: {step_ctx.get('explanation', 'N/A')}
  Variables in scope:
{locals_str}

FULL SOLUTION CODE:
```python
{problem.solution_code}
```

RULES:
- Answer ONLY about this problem and code.
- When referring to variables, mention their current values from the scope above.
- Keep answers concise (max 120 words) but thorough.
- If asked about a different step, explain based on the code context.
- Use plain text only — no markdown headers, no bullet symbols, just clean sentences.
- If the user asks "why", explain the algorithm logic, not just what the line does."""


# ═══════════════════════════════════════════════════════════
#  ASYNC DB HELPERS  (ORM calls must be wrapped in sync_to_async)
# ═══════════════════════════════════════════════════════════

@sync_to_async
def _get_problem(slug: str):
    """Fetch a single Problem by slug, or raise 404."""
    from django.shortcuts import get_object_or_404
    return get_object_or_404(Problem, slug=slug)


@sync_to_async
def _get_all_problems():
    return list(Problem.objects.all().order_by('leetcode_id'))


@sync_to_async
def _save_problem_fields(problem, fields: list):
    problem.save(update_fields=fields)


# ═══════════════════════════════════════════════════════════
#  ASYNC EXPLANATION GENERATOR
# ═══════════════════════════════════════════════════════════

async def generate_explanation_async(problem: Problem):
    """
    Concurrently generates EN explanation, HI explanation, and
    pattern analysis — only for fields that are not yet cached.
    Saves the results back to the DB.
    """
    print(f"\n{'─'*60}")
    print(f"  [explanation] Generating for: {problem.leetcode_id}. {problem.title}")

    tasks   = {}   # field_name -> coroutine
    results = {}

    if not problem.code_explanation:
        tasks['code_explanation'] = _call_groq_async(_english_prompt(problem))

    if not problem.code_explanation_hi:
        tasks['code_explanation_hi'] = _call_groq_async(_hindi_prompt(problem))

    if not problem.code_pattern:
        tasks['code_pattern'] = _call_groq_async(_pattern_prompt(problem))

    if not tasks:
        print(f"  [explanation] All fields already cached — skipping Groq calls.")
        print(f"{'─'*60}\n")
        return

    # Run all pending Groq calls concurrently
    keys   = list(tasks.keys())
    values = await asyncio.gather(*[tasks[k] for k in keys])

    fields_to_save = []
    for key, value in zip(keys, values):
        setattr(problem, key, value)
        fields_to_save.append(key)
        print(f"  [explanation] {key} done ({len(value)} chars)")

    await _save_problem_fields(problem, fields_to_save)
    print(f"  [explanation] Saved to DB: {fields_to_save}")
    print(f"{'─'*60}\n")


# ═══════════════════════════════════════════════════════════
#  VIEWS
# ═══════════════════════════════════════════════════════════

# ── index ──────────────────────────────────────────────────
async def index(request):
    problems = await _get_all_problems()
    return render(request, 'visualizer/index.html', {'problems': problems})


# ── detail ─────────────────────────────────────────────────
async def detail(request, slug):
    problem  = await _get_problem(slug)
    problems = await _get_all_problems()

    print(f"\n{'='*60}")
    print(f"  [detail] slug={slug}  "
          f"has_en={bool(problem.code_explanation)}  "
          f"has_hi={bool(problem.code_explanation_hi)}  "
          f"has_pattern={bool(problem.code_pattern)}")

    needs_gen = (
        not problem.code_explanation
        or not problem.code_explanation_hi
        or not problem.code_pattern
    )

    if needs_gen:
        try:
            await generate_explanation_async(problem)
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
        'problem':  problem,
        'problems': problems,
    })


# ── get_explanation ────────────────────────────────────────
@csrf_exempt
async def get_explanation(request, slug):
    if request.method != "GET":
        return JsonResponse({'error': 'GET only'}, status=405)

    problem = await _get_problem(slug)
    lang    = request.GET.get('lang', 'en')
    text    = problem.code_explanation_hi if lang == 'hi' else problem.code_explanation
    return JsonResponse({'text': text, 'lang': lang})


# ── get_pattern ────────────────────────────────────────────
@csrf_exempt
async def get_pattern(request, slug):
    if request.method != "GET":
        return JsonResponse({'error': 'GET only'}, status=405)

    problem = await _get_problem(slug)
    return JsonResponse({'text': problem.code_pattern or '', 'slug': slug})


# ── run_code ───────────────────────────────────────────────
@csrf_exempt
async def run_code(request, slug):
    if request.method != "POST":
        return JsonResponse({'error': 'POST only'}, status=405)

    try:
        data      = json.loads(request.body)
        raw_input = data.get('input', '').strip()
        tc_index  = int(data.get('test_case_index', 0))
        problem   = await _get_problem(slug)

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

        # execute_with_trace is CPU-bound — run it in a thread pool
        # so it does not block the async event loop
        steps, output, error = await asyncio.get_event_loop().run_in_executor(
            None, execute_with_trace, problem.solution_code, test_case
        )

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


# ── chat_step ──────────────────────────────────────────────
@csrf_exempt
async def chat_step(request, slug):
    """
    Accepts: { message, step_context: { line, explanation, locals, function_name }, history }
    Returns: { reply }
    """
    if request.method != "POST":
        return JsonResponse({'error': 'POST only'}, status=405)

    try:
        data         = json.loads(request.body)
        user_message = data.get('message', '').strip()
        step_ctx     = data.get('step_context', {})
        history      = data.get('history', [])
        problem      = await _get_problem(slug)

        if not user_message:
            return JsonResponse({'success': False, 'error': 'Empty message'})

        locals_str = (
            json.dumps(step_ctx.get('locals', {}), indent=2)
            if step_ctx.get('locals')
            else 'none'
        )

        system = _chat_system_prompt(problem, step_ctx, locals_str)

        # Keep last 12 messages (6 turns) for context window economy
        trimmed_history = history[-12:]
        messages = [{"role": m["role"], "content": m["content"]} for m in trimmed_history]
        messages.append({"role": "user", "content": user_message})

        reply = await _call_groq_chat_async(system, messages, max_tokens=300)

        return JsonResponse({'success': True, 'reply': reply})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})


# ═══════════════════════════════════════════════════════════
#  UTILITY / ERROR VIEWS
# ═══════════════════════════════════════════════════════════

async def get_steps(request, slug):
    await _get_problem(slug)   # validates slug exists
    return JsonResponse({'steps': []})


def error_500_preview(request):
    return render(request, '500.html', status=500)


def error_404_preview(request):
    return render(request, '404.html', status=404)


def custom_404(request, exception):
    return render(request, '404.html', status=404)