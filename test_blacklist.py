"""
Test script to debug blacklist filtering.
"""
import os
from supabase_client import get_supabase_client

# Test article
test_article = {
    'title': 'Influencers maken veel geld',
    'description': 'Dit artikel gaat over influencers en hun verdiensten.',
    'full_content': 'Influencers zijn mensen die geld verdienen op sociale media.'
}

# Test blacklist
blacklist = ['influencers', 'influencer']

print("=" * 60)
print("TESTING BLACKLIST FILTERING")
print("=" * 60)

print(f"\nTest article:")
print(f"  Title: {test_article['title']}")
print(f"  Description: {test_article['description']}")
print(f"  Full content: {test_article['full_content']}")

print(f"\nBlacklist keywords: {blacklist}")

# Test filtering logic
title = (test_article.get('title') or '').lower()
description = (test_article.get('description') or '').lower()
full_content = (test_article.get('full_content') or '').lower()

all_text = f"{title} {description} {full_content}"

print(f"\nCombined text (lowercase): {all_text}")

should_include = True
for keyword in blacklist:
    keyword_lower = keyword.lower().strip()
    print(f"\nChecking keyword: '{keyword_lower}'")
    if keyword_lower and keyword_lower in all_text:
        print(f"  ❌ FOUND in text - article should be FILTERED OUT")
        should_include = False
        break
    else:
        print(f"  ✓ Not found")

if should_include:
    print(f"\n✅ Article should be INCLUDED")
else:
    print(f"\n❌ Article should be FILTERED OUT")

