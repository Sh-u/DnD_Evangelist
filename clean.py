import requests
url = 'https://api.jsonbin.io/v3/b/645fcee29d312622a35d8d98'
headers = {
    'Content-Type': 'application/json',
    'X-Master-Key': '$2b$10$W6rtyWrgUBQ0wgXdw5yXP./6Kq/RugyU6cQyQyzGbLg4bcu.2tMvq'
}


req = requests.get(url, headers=headers)
req = req.json()

old = req['record']['signs']

print(f"old len: {len(old)}, old: {old} \n\n\n\n\n\n\n\n")


filtered = [obj for obj in req['record']
            ['signs'] if obj['date'] >= '2023-05-19 18:40:00']


print(f"filtered len: {len(filtered)}, filtered: {filtered}")

req = {
    "words": req['record']['words'],
    "signs": filtered
}


req2 = requests.put(url, json=req,  headers=headers)


print(f"\n\n\n\n\n\n\n {req2.json()}")
