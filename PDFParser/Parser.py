from ParserBase import ParserBase
import pdfplumber
import os
from statistics import median
import time

UPLOAD_EXTENSIONS = ['.pdf']

class PDFParser(ParserBase):
    
    def __init__(self, data):
        pdf = pdfplumber.open(data)

        if len(pdf.pages) == 0:
            pdf.close()
            raise "PDF file is invalid"

        pdf.close()
        self.data = data
        super(PDFParser, self).__init__()
        
    def parse(self):
        json_resp = []
        pdf = pdfplumber.open(self.data)

        for page in pdf.pages:
            # Extracting tables from pdf then removing them from the page.
            tables = self._extract_tables(page)
            page = self._remove_tables(page, tables)

            # Extracting images
            images = self._extract_images(page)

            # Extracting text
            sentences = self._extract_sentences(page)
            text_json = self._sentences_to_json(sentences)

            # Detect titles
            text_json = self._detect_titles(text_json)

            for item in [*tables, *images]:
                for i in range(len(text_json)):
                    if text_json[i]['top'] > item['top']:
                        text_json.insert(i, item)
                        break

            json_resp = [*json_resp, *[j['json'] for j in text_json]]
            self.page_number += 1

        pdf.close()
        
        self.parsed_data = json_resp
        return super(PDFParser, self).parse()

    def _detect_titles(self, text_json):
        sizes = set([t['size'] for t in text_json])
        thresh_size = median(sizes)*1.1

        for i in range(len(text_json)):
            if text_json[i]['size'] > thresh_size:
                text_json[i]['json']['datatype'] = 'title'
        return text_json

    def _is_diff_sentence(self, prev_sentence, next_sentence):
        return (next_sentence['top'] - prev_sentence['bottom'] > 10) or abs(next_sentence['size'] - prev_sentence['size']) > 3

    def _sentences_to_json(self, sentences):
        json_resp = []
        
        for sentence in sentences:
            text = sentence['text']
            if 'bold' in sentence['fontname'].lower():
                text = f"**{text}**" 
            if 'italic' in sentence['fontname'].lower():
                text = f"*{text}*" 

            if len(json_resp) == 0 or self._is_diff_sentence(json_resp[-1], sentence):
                json_resp.append({
                        'json': self._text_to_json(text),
                        'x0': sentence['x0'],
                        'top': sentence['top'],
                        'x1': sentence['x1'],
                        'bottom': sentence['bottom'],
                        'size': sentence['size']
                    })
            else:
                json_resp[-1]['json']['text'] += ' '+text
                json_resp[-1]['x0'] = min(json_resp[-1]['x0'], sentence['x0'])
                json_resp[-1]['top'] = min(json_resp[-1]['top'], sentence['top'])
                json_resp[-1]['x1'] = max(json_resp[-1]['x1'], sentence['x1'])
                json_resp[-1]['bottom'] = max(json_resp[-1]['bottom'], sentence['bottom'])
                json_resp[-1]['size'] = max(json_resp[-1]['size'], sentence['size'])

        return json_resp


    def _extract_sentences(self, page):
        sentences = []
        words = page.extract_words(extra_attrs=['size', 'fontname'], use_text_flow=True)
        for word in words:
            size = int(word['size']*1000)/1000
            if len(sentences) == 0 or \
                sentences[-1]['size'] != size or \
                    sentences[-1]['fontname'] != word['fontname'] or \
                        (word['top'] - sentences[-1]['bottom'] > 10):
                sentences.append({
                    'text': word['text'],
                    'size': size,
                    'fontname': word['fontname'],
                    'x0': word['x0'],
                    'top': word['top'],
                    'x1': word['x1'],
                    'bottom': word['bottom']
                })
            else:
                sentences[-1]['text'] += ' '+word['text']
                sentences[-1]['x0'] = min(sentences[-1]['x0'], word['x0'])
                sentences[-1]['top'] = min(sentences[-1]['top'], word['top'])
                sentences[-1]['x1'] = max(sentences[-1]['x1'], word['x1'])
                sentences[-1]['bottom'] = max(sentences[-1]['bottom'], word['bottom'])
        return sentences

    def _extract_images(self, page):
        json_resp = []
        for image in page.images:
            name = image['name']
            x0 = image['x0']
            top = image['top']
            x1 = image['x1']
            bottom = image['bottom']
            file_name = os.path.join(self.image_path, f'{name}-{int(time.time())}.png')
            with open(file_name, 'wb') as file:
                file.write(image['stream'].rawdata)

            json_resp.append({
                'json': self._file_to_json('image', file_name, name),
                'x0': x0,
                'top': top,
                'x1': x1,
                'bottom': bottom
            })
        return json_resp


    def _extract_tables(self, page):
        json_resp = []
        tables = page.extract_tables()
        edges = page.debug_tablefinder().tables
        for i in range(len(tables)):
            json_resp.append({
                'json': self._table_to_json(tables[i][0], tables[i][1:]),
                'x0': min([e[0] for e in edges[i].cells]),
                'top': min([e[1] for e in edges[i].cells]),
                'x1': max([e[2] for e in edges[i].cells]),
                'bottom': max([e[3] for e in edges[i].cells])
            })
            
        return json_resp

    def _remove_tables(self, page, tables_json):
        for table in tables_json:
            page = page.outside_bbox((table['x0'], table['top'], table['x1'], table['bottom']))
        return page
        
        