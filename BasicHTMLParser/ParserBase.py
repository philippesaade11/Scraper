from abc import ABC, abstractmethod
import uuid

class ParserBase(ABC):
    group_id = str(uuid.uuid4()) # This groups multiple datatypes together, e.g. in RSS feeds a group defines an item, in a word document it defines a page.
    page_number = 0
    image_path = 'static/'
    urls = []
    parsed_data = []
    
    def parse(self):
        return {
            'data': self.parsed_data,
            'urls': self.urls
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