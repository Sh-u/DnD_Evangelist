import threading
import queue
import requests


q = queue.Queue()

with open('proxyList.txt', 'r') as f:
    for line in f:
        line = line.rstrip()
        q.put(line)


def checkValidProxy():
    global q
    while not q.empty():
        proxy = q.get()
        try:
            res = requests.get("http://ipinfo.io/json",
                               proxies={"http": proxy, "https": proxy})
        except:
            continue
        if res.status_code == 200:
            print(proxy)


for _ in range(10):
    threading.Thread(target=checkValidProxy).start()
