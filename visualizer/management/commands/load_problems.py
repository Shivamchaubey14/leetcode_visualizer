from django.core.management.base import BaseCommand
from visualizer.models import Problem

class Command(BaseCommand):
    help = 'Load initial LeetCode problems'
    
    def handle(self, *args, **options):
        problems = [
            {
                'leetcode_id': 1,
                'title': 'Two Sum',
                'slug': 'two-sum',
                'category': 'array',
                'difficulty': 'easy',
                'description': 'Given an array of integers nums and an integer target, return indices of the two numbers that add up to target.',
                'solution_code': '''def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []

# Test case
nums = [2, 7, 11, 15]
target = 9
result = two_sum(nums, target)
print(f"Indices: {result}")''',
                'test_cases': ['[2,7,11,15],9', '[3,2,4],6', '[3,3],6']
            },
            {
                'leetcode_id': 3,
                'title': 'Longest Substring Without Repeating Characters',
                'slug': 'longest-substring',
                'category': 'string',
                'difficulty': 'medium',
                'description': 'Find the length of the longest substring without repeating characters.',
                'solution_code': '''def length_of_longest_substring(s):
    char_set = set()
    left = 0
    max_length = 0
    
    for right in range(len(s)):
        while s[right] in char_set:
            char_set.remove(s[left])
            left += 1
        char_set.add(s[right])
        max_length = max(max_length, right - left + 1)
    
    return max_length

# Test
s = "abcabcbb"
result = length_of_longest_substring(s)
print(f"Length: {result}")''',
                'test_cases': ['"abcabcbb"', '"bbbbb"', '"pwwkew"']
            }
        ]
        
        for prob_data in problems:
            Problem.objects.get_or_create(
                leetcode_id=prob_data['leetcode_id'],
                defaults=prob_data
            )
            self.stdout.write(f"Loaded: {prob_data['title']}")