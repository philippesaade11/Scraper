import requests

def test_rss():
    r = requests.post('http://localhost:8000/parse', files = {'data': open('C:\\Users\\96181\\Desktop\\Convaise IDP\\examples\\example-rss.xml','rb')})
    return r.json()