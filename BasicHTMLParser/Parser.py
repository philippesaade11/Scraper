from ParserBase import ParserBase
import lxml.html
from lxml import etree
import os
import requests
import pandas as pd
import time

UPLOAD_EXTENSIONS = ['.html', '.htm']

class BasicHTMLParser(ParserBase):
    """
    Basic HTML Parser that takes html tags as a string and outputs the processed json data
    
    """
    non_text_tags = ['table', 'ul', 'ol', 'img', 'svg', 'audio', 'video']

    def __init__(self, data):

        # Check if data is valid HTML
        if lxml.html.fromstring(data).find('.//*') is not None:
            self.data = data
            
        # Check if data is a file location
        elif os.path.exists(data):
            with open(data, 'r', encoding='utf-8') as file:
                self.data = file.read()
        
        # Check if data is a url
        else:
            try:
                r = requests.get(data)
                self.data = r.content
            except:
                raise "Data is not HTML, a valid file location, or a URL"

        if lxml.html.fromstring(self.data).find('.//*') is None:
            raise "Data content is not valid HTML"

        super(BasicHTMLParser, self).__init__()
                
    def parse(self, include_iframe=False):
        if include_iframe:
            self.non_text_tags += ['iframe']

        html = etree.HTML(self.data)
        elements = self._get_relevant_elements(html)
        self.parsed_data = list(filter(None, [self._element_to_json(el) for el in elements]))

        self.urls = self._get_all_urls(html)
        return super(BasicHTMLParser, self).parse()

    def _element_to_json(self, el):
        if el.tag == 'img':
            image_url = el.attrib.get('src', '')
            image_name = el.attrib.get('alt', el.attrib.get('aria-label', ''))
            image_name = self._get_url(image_name, el)
            return self._file_to_json('image', image_url, image_name, tag=el.tag)
            
        elif el.tag == 'svg':
            image_name = ''
            image_url = os.path.join(self.image_path, f'{image_name}{int(time.time())}.svg')
            with open(image_url, "wb") as out:
                out.write(etree.tostring(el))
            return self._file_to_json('image', image_url, image_name, tag=el.tag)

        elif (el.tag == 'audio') or (el.tag == 'video'):
            file_name = self._element_to_text(el)
            file_url = el.attrib.get('src', '')
            if (file_url == '') and (len(el.xpath('.//source')) > 0):
                file_url = el.xpath('.//source')[0].attrib.get('src', '')
            return self._file_to_json(el.tag, file_url, file_name, tag=el.tag)

        elif el.tag == 'iframe':
            file_name = self._element_to_text(el)
            file_url = el.attrib.get('src', '')
            return self._file_to_json('iframe', file_url, file_name, tag=el.tag)
        
        elif el.tag == 'ul' or el.tag == 'ol' or el.tag == 'dl':
            list_elements = [self._element_to_text(li) for li in el.xpath('.//*[name() = "li" or name() = "dd" or name() = "dt"]')]
            return self._list_to_json(list_elements, tag=el.tag)
        
        elif el.tag == 'table':
            table = pd.read_html(lxml.html.tostring(el))[0]
            return self._table_to_json(table.columns.values.tolist(), table.to_dict(orient='records'), tag=el.tag)
        
        elif self._element_is_title(el):
            text = self._element_to_text(el)
            return self._title_to_json(text, tag=el.tag)
        
        elif self._element_is_text(el):
            text = self._element_to_text(el)
            return self._text_to_json(text, tag=el.tag)
        
    def _get_relevant_elements(self, html):
        
        # Tags that are not text, including lists, tables and images
        non_text_condition = ' or '.join([f'(name() = "{t}")' for t in self.non_text_tags])
        
        # Get tags which have text but their ancestors don't. The largest tags in heirarchy which have text
        text_condition = 'normalize-space(text()) and not(ancestor::*[normalize-space(text())])'
        
        # We also want to remove text tags which are in lists, tables...
        non_text_ancestor_condition = ' and '.join([f'not(ancestor::{t})' for t in self.non_text_tags]) 

        # Combine the text and non text conditions
        final_xpath = f'.//*[({text_condition} and {non_text_ancestor_condition}) or {non_text_condition}]'

        return html.xpath(final_xpath)

    def _element_to_text(self, el):
        text = (el.text.strip() if el.text is not None else '') + ' '.join([self._element_to_text(child) for child in el])
        if el.tag == 'a':
            text = f'[{text}]({el.attrib.get("href", "")})'
        elif el.tag == 'strong' or el.tag == 'b':
            text = f'**{text}**'
        elif el.tag == 'em' or el.tag == 'i':
            text = f'*{text}*'
        text +=  (' '+el.tail.strip() if el.tail is not None else '')
        return text.strip()

    def _element_is_title(self, el):
        return (el.tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'title', 'caption', 'label', 'legend']) \
            or ('title' in el.attrib.get('class', '')) \
            or ('caption' in el.attrib.get('class', ''))
            # or (self._element_is_text(el) and len(el) == 0 and len(el.text) < 50)

    def _element_is_text(self, el):
        return el.tag in ['p', 'article', 'span', 'div', 'blockquote', 'main', 'section', 'aside', 'header', 'footer']

    def _get_url(self, text, el):
        links = el.xpath('.//ancestor::a[@href]')
        if len(links) > 0:
            text = f"[{text}]({links[0].attrib.get('href', '')})"
        return text

    def _get_all_urls(self, html):
        links = html.xpath('.//a[@href]')
        return [link.attrib.get('href', '') for link in links]