import requests
url = 'https://api.jsonbin.io/v3/b/645fcee29d312622a35d8d98'
headers = {
    'Content-Type': 'application/json',
    'X-Master-Key': '$2b$10$W6rtyWrgUBQ0wgXdw5yXP./6Kq/RugyU6cQyQyzGbLg4bcu.2tMvq'
}


req = requests.get(url, headers=headers)
req = req.json()


# filtered = [obj for obj in req['record']
#             ['signs'] if obj['date'] >= '2023-05-1


req = {
    "words": req['record']['record']['words'],
    "signs": req['record']['record']['signs']
}


req2 = requests.put(url, json=req,  headers=headers)


print(f"\n\n\n\n\n\n\n {req2.json()}")
