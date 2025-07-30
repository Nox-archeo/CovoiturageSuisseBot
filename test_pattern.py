#!/usr/bin/env python3
import re

# Test du pattern modifié
pattern = r'^menu:(?!profile$|create$).*'

test_cases = [
    'menu:create',
    'menu:profile', 
    'menu:search_trip',
    'menu:my_trips',
    'menu:help'
]

print('🔍 Test du pattern:', pattern)
print('=' * 50)
for test in test_cases:
    match = re.match(pattern, test)
    result = '✅ MATCH' if match else '❌ NO MATCH'
    print(f'  {test}: {result}')

print('\n📋 Résultat attendu:')
print('  - menu:create et menu:profile doivent être ❌ NO MATCH')
print('  - Les autres doivent être ✅ MATCH')
