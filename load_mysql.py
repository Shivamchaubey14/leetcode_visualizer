import os
import django
import json

os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
django.setup()

from visualizer.models import Problem

with open('datadump_raw.json', 'r', encoding='utf-8') as f:
    problems = json.load(f)

count = 0
for p in problems:
    p.pop('id', None)
    obj, created = Problem.objects.get_or_create(
        slug=p['slug'],
        defaults=p
    )
    if created:
        count += 1
        print('  Created: ' + p['title'])
    else:
        print('  Skipped (exists): ' + p['title'])

print('Done — ' + str(count) + ' new problems inserted into MySQL')