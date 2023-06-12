import requests
url = 'https://api.jsonbin.io/v3/b/6471ecb08e4aa6225ea50e5a'
headers = {
    'Content-Type': 'application/json',
    'X-Master-Key': '$2b$10$3hURQWbRma8hTGF8WLMRtuNN0pbk56nyDcrq/SlAfcSAvW2LZoOl.'
}


req = requests.get(url, headers=headers)
req = req.json()

old = req['record']['signs']

print(f"old len: {len(old)}, old: {old} \n\n\n\n\n\n\n\n")


filtered = [obj for obj in req['record']
            ['signs'] if obj['date'] >= '2023-06-04']


print(f"filtered len: {len(filtered)}, filtered: {filtered}")

req = {
    "words": req['record']['words'],
    "signs": filtered
}


req2 = requests.put(url, json=req,  headers=headers)


print(f"\n\n\n\n\n\n\n {req2.json()}")
