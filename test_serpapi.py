# test_serpapi.py
from serpapi import GoogleSearch

params = {
    "q": "OpenAI",
    "api_key": "aea58880b4874927e429f847abed9bbe50e1123209da76b153faa1160872d3e1",  # Replace with your real key
}

search = GoogleSearch(params)
results = search.get_dict()

print("✅ SerpAPI working! Results:")
print(results)
