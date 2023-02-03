import mimetypes
import requests
import logging
import re
import os

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

class Crawler(object):

    def __init__(self, start_url, parsers, max_depth=3, headers={}, url_regex='.*', parse_images=False):
        self.parsed_url = []
        self.url = [start_url]
        self.parsers = parsers
        self.headers = headers
        self.depth = 0
        self.max_depth = max_depth
        self.url_regex = re.compile(url_regex)
        self.parse_images = parse_images
        self.messages = []
        self.json_resp = []
        
    def parse(self):
        while len(self.url) > 0 and self.depth < self.max_depth:
            new_urls = []
            while len(self.url) > 0:
                current_url = self.url.pop()
                if current_url in self.parsed_url:
                    logging.info(f'{current_url} already parsed')
                    continue
                if self.depth > 0 and not bool(re.match(self.url_regex, current_url)):
                    logging.info(f'{current_url} skipped')
                    continue
                logging.info(f'Parsing URL {current_url}')

                resp = self.parse_url(current_url)
                self.parsed_url.append(current_url)
                if 'urls' in resp:
                    new_urls = [*new_urls, *resp['urls']]
                if 'data' in resp:
                    self.json_resp = [*self.json_resp, {'data': resp['data'], 'url': current_url, 'depth': self.depth}]

            self.depth += 1
            self.url = new_urls
            logging.info(f'Depth {self.depth} is done, {len(self.parsed_url)} parsed urls, {len(self.url)} future urls')

        logging.info(f'Parsing Finished with {len(self.parsed_url)} parsed urls')
        return self.json_resp

    def parse_url(self, url):
        content_type = mimetypes.guess_type(url.split('?')[0])[0]
        if content_type is None:
            try:
                r = requests.head(url, headers=self.headers, allow_redirects=True)
                content_type = r.headers["content-type"]
            except:
                logging.error(f'URL {url} is not responding')
                return {'data': 'error: url not responding'}

        file_ext = mimetypes.guess_extension(content_type.split(";")[0])
        is_file = os.path.exists(url)

        for parser in self.parsers:
            if file_ext in parser['file_extensions']:
                try:
                    if is_file:
                        r = requests.post(f'http://{parser["name"]}:{parser["port"]}/parse', files = {'data': open(url, "rb"), 'add_images': self.parse_images})
                    else:
                        r = requests.post(f'http://{parser["name"]}:{parser["port"]}/parse', data = {'data': url, 'add_images': self.parse_images})
                    
                    assert r.status_code == 200
                    return r.json()
                except Exception as e:
                    logging.error(f'Parser {parser["name"]} is not responding')
                    return {'data': f'error: {str(e)}'}

        logging.info(f'URL {url} unknown content type')
        return {'data': 'error: unknown content type'}
