# visualizer/admin.py
import json
from django import forms
from django.contrib import admin
from django.utils.html import format_html, mark_safe
from .models import Problem


# ─────────────────────────────────────────────────────────────
#  Test-case format reference shown inside the admin
# ─────────────────────────────────────────────────────────────
TEST_CASE_HELP = """
<div style="font-family:monospace;font-size:12px;line-height:1.7;
            background:#1e1e2e;color:#cdd6f4;padding:14px 16px;
            border-radius:6px;border:1px solid #313244;margin-top:8px;">

<b style="color:#cba6f7">FORMAT</b> — JSON array, one object per test case:<br><br>

<b style="color:#89b4fa">Simple values</b> (twoSum, etc.)<br>
<span style="color:#a6e3a1">[{"args": [[2,7,11,15], 9]},
 {"args": [[3,2,4], 6]}]</span><br><br>

<b style="color:#89b4fa">String problems</b> (lengthOfLongestSubstring, etc.)<br>
<span style="color:#a6e3a1">[{"args": ["abcabcbb"]},
 {"args": ["bbbbb"]}]</span><br><br>

<b style="color:#89b4fa">Linked list problems</b> (addTwoNumbers, etc.)<br>
<span style="color:#a6e3a1">[{"args": [[2,4,3], [5,6,4]], "linked_list_args": [0,1]},
 {"args": [[0],   [0]],   "linked_list_args": [0,1]}]</span><br>
<span style="color:#6c7086"># "linked_list_args": indices of args to auto-convert to LinkedList</span><br><br>

<b style="color:#89b4fa">Tree problems</b> (maxDepth, etc.)<br>
<span style="color:#a6e3a1">[{"args": [[3,9,20,null,null,15,7]], "tree_args": [0]},
 {"args": [[1,null,2,3]],        "tree_args": [0]}]</span><br>
<span style="color:#6c7086"># "tree_args": indices of args to auto-convert to TreeNode (level-order list)</span><br><br>

<b style="color:#89b4fa">Matrix / 2-D grid problems</b><br>
<span style="color:#a6e3a1">[{"args": [[[1,3],[2,6],[8,10],[15,18]]]}]</span><br><br>

<b style="color:#89b4fa">Optional override: expected output</b><br>
<span style="color:#a6e3a1">[{"args": [[2,7,11,15], 9], "expected": [0,1]}]</span>
</div>
"""


class ProblemAdminForm(forms.ModelForm):
    test_cases = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 14,
            'style': (
                'font-family: "Fira Code", "Courier New", monospace;'
                'font-size: 13px;'
                'background: #1e1e2e;'
                'color: #cdd6f4;'
                'border: 1px solid #313244;'
                'border-radius: 6px;'
                'padding: 10px 12px;'
                'width: 100%;'
            ),
            'placeholder': '[{"args": [[2,7,11,15], 9]}, {"args": [[3,2,4], 6]}]',
            'spellcheck': 'false',
        }),
        required=False,
        initial='[]',
        label='Test cases (JSON)',
    )

    class Meta:
        model  = Problem
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 8}),
            'solution_code': forms.Textarea(attrs={
                'rows': 20,
                'style': (
                    'font-family: "Fira Code", "Courier New", monospace;'
                    'font-size: 13px;'
                ),
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ── FIX: always serialize the stored Python object back to a
        #    proper JSON string so the textarea shows double-quoted JSON,
        #    not Python's repr (single quotes, True/False/None).
        if self.instance and self.instance.pk:
            raw = self.instance.test_cases
            if raw is not None:
                # json.dumps produces real JSON: double quotes, true/false/null
                self.initial['test_cases'] = json.dumps(raw, indent=2, ensure_ascii=False)
            else:
                self.initial['test_cases'] = '[]'

    # ── Validation ──────────────────────────────────────────
    def clean_test_cases(self):
        value = self.cleaned_data.get('test_cases', '').strip()
        if not value:
            return []
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as e:
            raise forms.ValidationError(f'Invalid JSON — {e}')

        if not isinstance(parsed, list):
            raise forms.ValidationError(
                'Test cases must be a JSON array: [ {…}, {…} ]'
            )

        errors = []
        for i, tc in enumerate(parsed):
            if not isinstance(tc, dict):
                errors.append(f'Item {i}: must be a JSON object {{ … }}')
                continue
            if 'args' not in tc:
                errors.append(
                    f'Item {i}: missing "args" key. '
                    f'Minimum: {{"args": [arg1, arg2, ...]}}'
                )
                continue
            if not isinstance(tc['args'], list):
                errors.append(f'Item {i}: "args" must be a list.')
            # Validate optional converter keys
            for key in ('linked_list_args', 'tree_args'):
                if key in tc:
                    if not isinstance(tc[key], list):
                        errors.append(f'Item {i}: "{key}" must be a list of argument indices.')
                    elif not all(isinstance(x, int) for x in tc[key]):
                        errors.append(f'Item {i}: "{key}" must contain integers only.')

        if errors:
            raise forms.ValidationError(errors)

        return parsed

    def clean_leetcode_id(self):
        value = self.cleaned_data.get('leetcode_id')
        if value is not None and value < 1:
            raise forms.ValidationError('LeetCode ID must be a positive integer.')
        return value


# ─────────────────────────────────────────────────────────────
#  Admin registration
# ─────────────────────────────────────────────────────────────
@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    form = ProblemAdminForm

    # ── List view ────────────────────────────────────────────
    list_display  = [
        'leetcode_id', 'title', 'colored_difficulty',
        'category', 'test_case_count', 'created_at',
    ]
    list_filter   = ['difficulty', 'category']
    search_fields = ['title', 'leetcode_id']
    ordering      = ['leetcode_id']
    prepopulated_fields = {'slug': ('title',)}

    # ── Detail view ──────────────────────────────────────────
    readonly_fields = ('created_at', 'test_case_help_text')

    fieldsets = (
        ('Identity', {
            'fields': ('leetcode_id', 'title', 'slug', 'category', 'difficulty'),
        }),
        ('Content', {
            'fields': ('description', 'solution_code'),
        }),
        ('Test Cases', {
            'fields': ('test_case_help_text', 'test_cases'),
            'description': 'Define inputs that will be run through the tracer.',
        }),
        ('Meta', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    # ── Custom columns ───────────────────────────────────────
    @admin.display(description='Difficulty')
    def colored_difficulty(self, obj):
        colors = {'easy': '#2db55d', 'medium': '#f5a623', 'hard': '#e05252'}
        color  = colors.get(obj.difficulty, '#888')
        return format_html(
            '<span style="color:{};font-weight:700;text-transform:capitalize">{}</span>',
            color,
            obj.get_difficulty_display(),
        )

    @admin.display(description='Test cases')
    def test_case_count(self, obj):
        n = len(obj.test_cases) if obj.test_cases else 0
        color = '#2db55d' if n else '#888'
        return format_html(
            '<span style="color:{};font-weight:600">{} case{}</span>',
            color, n, '' if n == 1 else 's',
        )

    @admin.display(description='')
    def test_case_help_text(self, obj):
        return mark_safe(TEST_CASE_HELP)