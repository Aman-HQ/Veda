import re

# Test the regex pattern used in moderation
keywords = ['suicide', 'kill', 'die', 'chest pain']

for keyword in keywords:
    pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
    compiled = re.compile(pattern, re.IGNORECASE)
    
    # Test cases
    tests = [
        'I want to commit suicide',
        'i want to kil someone',
        'die',
        'I have chest pain',
        'kill',
        'Can I kil someone'  # typo
    ]
    
    print(f'\nKeyword: {keyword}')
    print(f'Pattern: {pattern}')
    for test in tests:
        matches = compiled.findall(test.lower())
        if matches:
            print(f'  ✓ Matched in: "{test}" -> {matches}')
