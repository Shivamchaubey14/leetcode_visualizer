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
        data = json.loads(request.body)
        user_input = data.get('input', '')
        problem = get_object_or_404(Problem, slug=slug)

        steps, output, error = execute_with_trace(problem.solution_code, user_input)

        return JsonResponse({
            'success': True,
            'steps': steps,
            'output': output,
            'error': error,
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
        })


def get_steps(request, slug):
    """Return pre-computed steps for a problem (cacheable in production)."""
    problem = get_object_or_404(Problem, slug=slug)
    return JsonResponse({'steps': []})