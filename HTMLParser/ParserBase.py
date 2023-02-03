from abc import ABC
import uuid
import os

class ParserBase(ABC):
    group_id = str(uuid.uuid4()) # This groups multiple datatypes together, e.g. in RSS feeds a group defines an item, in a word document it defines a page.
    page_number = 0
    image_path = 'static/'
    image_serve_url = 'http://main:5000/getimage/'
    parser_name = ''
    urls = []
    file_urls = []
    parsed_data = []
    
    def parse(self, add_files=False):
        return {
            'data': self.parsed_data,
            'urls': self.urls + (self.file_urls if add_files else [])
        }

    def _new_group(self):
        self.group_id = str(uuid.uuid4())

    def _list_to_json(self, list_content, tag=''):
        return {
            'datatype': 'list',
            'content': list_content,
            'tag': tag,
            'group_id': self.group_id, 
            'page': self.page_number
        }

    def _title_to_json(self, title, tag=''):
        return {
            'datatype': 'title',
            'text': title,
            'tag': tag,
            'group_id': self.group_id, 
            'page': self.page_number
        }

    def _text_to_json(self, text, tag=''):
        return {
            'datatype': 'text',
            'text': text,
            'tag': tag,
            'group_id': self.group_id, 
            'page': self.page_number
        }

    def _file_to_json(self, file_type, url, name, tag=''):
        if os.path.exists(url):
            url = self.image_serve_url + os.path.split(url)[1] + "?parser=" + self.parser_name
        self.file_urls.append(url)
        return {
            'datatype': file_type,
            'url': url,
            'name': name,
            'tag': tag,
            'group_id': self.group_id, 
            'page': self.page_number
        }

    def _table_to_json(self, table_headers, table_content, tag=''):
        return {
            'datatype': 'table',
            'headers': table_headers,
            'content': table_content,
            'tag': tag,
            'group_id': self.group_id, 
            'page': self.page_number
        }