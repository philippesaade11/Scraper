from mimetypes import guess_extension
import json
import requests

class Crawler(object):
    
    def __init__(self, start_url, parsers, max_depth=5, headers={}, url_regex='.*'):
        self.parsed_url = []
        self.url = [start_url]
        self.parsers = parsers
        self.headers = headers
        self.depth = 0
        self.max_depth = max_depth
        self.url_regex = url_regex
        self.messages = []
        self.json_resp = []

    def parse(self):
        if len(self.url) <= 0 or self.depth >= self.max_depth:
            return self.json_resp
        
        new_urls = []
        while len(self.url) > 0:
            current_url = self.url.pop()
            resp = self.parse_url(current_url)

        self.depth += 1



    def parse_url(self, url):
        try:
            r = requests.get(url, headers=self.headers)
        except:
            self.messages.append({'type': 'error', 'message': f'URL {url} is not responding'})
            return {'urls': [], 'data': []}

        file_ext = guess_extension(r.headers["content-type"].split(";")[0])

        for parser in self.parsers:
            if file_ext in parser['file_extensions']:
                try:
                    r = requests.post(f'http://{parser["name"]}:{parser["port"]}/parse', data = {'data': url})
                    return r.json()
                except:
                    self.messages.append({'type': 'error', 'message': f'Parser {parser["name"]} is not responding'})
                return {'urls': [], 'data': []}

        self.messages.append({'type': 'error', 'message': f'URL {url} unknown content type'})
        return {'urls': [], 'data': []}

config = {}
with open("config.json") as outfile:
    config = json.load(outfile)