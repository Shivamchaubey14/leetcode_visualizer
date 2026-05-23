from django.db import models
from django.urls import reverse

class Problem(models.Model):
    CATEGORIES = [
        ('number', 'Number'),
        ('array', 'Array'),
        ('string', 'String'),
        ('tree', 'Tree'),
        ('dp', 'Dynamic Programming'),
        ('graph', 'Graph'),
        ('linkedlist', 'Linked List'),
    ]
    
    DIFFICULTY = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    leetcode_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.CharField(max_length=50, choices=CATEGORIES)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY)
    description = models.TextField()
    solution_code = models.TextField(help_text="Python solution code")
    test_cases = models.JSONField(default=list, help_text="List of test inputs")
    code_explanation = models.TextField(
        blank=True,
        default='',
        help_text="Step-by-step explanation of the solution (auto-generated or manual)"
    )
    code_explanation_hi = models.TextField(blank=True, default='', help_text="Hindi explanation (auto-generated)")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.leetcode_id}. {self.title}"
    
    def get_absolute_url(self):
        return reverse('detail', args=[self.slug])