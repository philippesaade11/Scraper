from ParserBase import ParserBase
import feedparser
import mimetypes

UPLOAD_EXTENSIONS = ['.rss', '.xml']

class RSSParser(ParserBase):
    
    def __init__(self, data):
        rssfeed = feedparser.parse(data)
        if len(rssfeed.entries) == 0:
            raise "RSS file is invalid"
        
        self.rssfeed = rssfeed
        super(RSSParser, self).__init__()
        
    def parse(self):
        json_resp = self._extract_title_text(self.rssfeed.feed)
        self.page_number += 1

        for entry in self.rssfeed.entries:
            entry_json = self._entry_to_json(entry)
            json_resp = [*json_resp, *entry_json]
            self.page_number += 1

        self.parsed_data = json_resp
        return super(RSSParser, self).parse()

    def _extract_title_text(self, obj):
        json_resp = []

        # Title elements
        if 'title' in obj:
            title = obj["title"]
            if 'link' in obj:
                title = f'[{title}]({obj["link"]})'
                self.urls.append(obj["link"])

            json_resp.append(self._title_to_json(title, tag='title'))
        
        # Text elements
        if 'summary' in obj:
            json_resp.append(self._text_to_json(obj['summary'], tag='description'))
        if 'subtitle' in obj:
            json_resp.append(self._text_to_json(obj['subtitle'], tag='description'))

        # List elements
        if 'tags' in obj:
            list_elements = [term.strip() for tag in obj['tags'] for term in tag['term'].split('/') if term.strip() != '']
            json_resp.append(self._list_to_json(list_elements, tag='category'))

        # Image elements
        if 'image' in obj:
            image_url = obj['image']['href']
            image_name = obj['image'].get('subtitle', obj['image'].get('title', None))
            json_resp.append(self._file_to_json('image', image_url, image_name))

        # Author
        if 'author' in obj:
            json_resp.append(self._text_to_json(obj['author'], tag='author'))

        # Publish Date
        if 'published' in obj:
            json_resp.append(self._text_to_json(obj['published'], tag='pubDate'))

        return json_resp
    
    def _entry_to_json(self, entry):
        json_resp = self._extract_title_text(entry)
        
        for link in entry['links']:
            media_type = mimetypes.guess_type(link['href'])[0]
            if media_type and (media_type.split('/')[0] in ['video', 'audio', 'image']):
                json_resp.append(self._file_to_json(media_type.split('/')[0], link['href'], ''))
        
        return json_resp