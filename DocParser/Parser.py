from ParserBase import ParserBase
from mimetypes import guess_extension
import os
import mammoth
import sys
import time
import requests
import subprocess

UPLOAD_EXTENSIONS = ['.doc', '.docx']

class DocParser(ParserBase):
    """
    Word Document Parser that transforms the documents into simple html pages then uses BasicHTMLParser to extract data.
    
    """
    parser_name = 'docparser'
    
    def __init__(self, data, html_parser_url):

        # Check if data is a file location
        if os.path.exists(data):
            self.data = data
        # Check if data is a url
        else:
            try:
                r = requests.get(data)
                file_ext = guess_extension(r.headers["content-type"].split(";")[0])
                file_name = f'/app/files/{int(time.time())}.' + file_ext
                with open(file_name, 'wb') as f:
                    f.write(r.content)
                self.data = file_name
            except:
                raise Exception("Data is not a valid file location or a URL")

        self.html_parser_url = html_parser_url

        extension = os.path.splitext(self.data)[1]
        if extension not in UPLOAD_EXTENSIONS:
            raise Exception(f"{extension} is not a valid file extension")

        # Transform doc to docx
        if extension == '.doc':
            # For windows operating systems
            if sys.platform.startswith('win'):
                from win32com import client as wc

                w = wc.Dispatch('Word.Application')
                doc = w.Documents.Open(self.data)
                doc.SaveAs(self.data+'x', 16)
                self.data = self.data+'x'
            
            # For other systems
            else:
                subprocess.call(['lowriter', '--convert-to', 'docx', '--outdir', os.path.dirname(self.data),  self.data])
                self.data = self.data+'x'

        super(DocParser, self).__init__()

    def convert_image(self, image):
        with image.open() as image_bytes:
            image_name = f'{image.alt_text+"-" if image.alt_text is not None else ""}{int(time.time())}{guess_extension(image.content_type)}'
            image_name = os.path.join(self.image_path, image_name)
            with open(image_name, 'wb') as file:
                file.write(image_bytes.read())

        return {
            "src": image_name
        }
                    
    def parse(self, add_images=False):
        with open(self.data, "rb") as docx_file:
            htmltrans = mammoth.convert_to_html(docx_file, convert_image=mammoth.images.img_element(self.convert_image))

        self.data = f'<html>{htmltrans.value}</html>'
        self.html_messages = htmltrans.messages

        json_resp = self._parse_basic_html(self.data)
        
        self.parsed_data = json_resp['data']
        self.urls = json_resp['urls']
        return super(DocParser, self).parse(add_files=add_images)

    def _parse_basic_html(self, html):
        json_resp = {}
        try:
            json_resp = requests.post(self.html_parser_url, data={'data': html})
            json_resp = json_resp.json()
        except:
            raise Exception("Basic HTML Parser not responding")
        return json_resp