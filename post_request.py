import requests

id="1WPLHhWKe52x4fuiPvRJTjmq6smelBeAP"
url=f"https://drive.google.com/uc?export=download&id={id}"
r=requests.get(url)
with open("img.jpg","wb")as f:
    f.write(r.content)


