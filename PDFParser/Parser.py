from ParserBase import ParserBase
import pdfplumber
import os
from statistics import median
import time
import re
import requests
import gc

UPLOAD_EXTENSIONS = ['.pdf']

class PDFParser(ParserBase):
    """
    PDF Parser
    
    """
    parser_name = 'pdfparser'
    
    def __init__(self, data):
        
        # Check if data is a file location
        if os.path.exists(data):
            self.data = data
        # Check if data is a url
        else:
            try:
                r = requests.get(data)
                file_name = f'./files/{int(time.time())}.pdf'
                with open(file_name, 'wb') as f:
                    f.write(r.content)
                self.data = file_name
            except:
                raise Exception("Data is not a valid file location or a URL")

        invalid = False
        try:
            with pdfplumber.open(self.data) as pdf:
                invalid = (pdf is None or len(pdf.pages) == 0)
            
            pdf.flush_cache()
            pdf.close()
            del pdf
            gc.collect()
        except:
            pass

        if invalid:
            raise Exception("PDF file is invalid")

        super(PDFParser, self).__init__()
        
    def parse(self, add_images=False):
        json_resp = []
        with pdfplumber.open(self.data) as pdf:
            for page in pdf.pages:
                # Extracting tables from pdf then removing them from the page.
                tables = self._extract_tables(page)
                page = self._remove_tables(page, tables)

                # Extracting images
                images = self._extract_images(page)

                # Extracting text
                text_json = []
                sentences = self._extract_sentences(page)
                if len(sentences) > 0:
                    text_json = self._sentences_to_json(sentences)

                    # Detect titles
                    text_json = self._detect_titles(text_json)
                        
                    # Detect lists
                    json_resp = self._detect_lists(json_resp)    

                for item in [*tables, *images]:
                    inserted = False
                    for i in range(len(text_json)):
                        if text_json[i]['top'] > item['top']:
                            text_json.insert(i, item)
                            inserted = True
                            break
                    if not inserted:
                        text_json.append(item)
                
                if len(text_json) == 0:
                    file_name = os.path.join(self.image_path, f'page{self.page_number}-{int(time.time())}.png')
                    page.to_image().save(file_name)
                    text_json = [{
                        'json': self._file_to_json('image', file_name, f'page {self.page_number}')
                    }]
                json_resp = [*json_resp, *[j['json'] for j in text_json]]    

                self.page_number += 1

        pdf.flush_cache()
        pdf.close()
        del pdf
        gc.collect()

        self.parsed_data = json_resp
        return super(PDFParser, self).parse(add_files=add_images)

    def _detect_titles(self, text_json):
        sizes = set([t['size'] for t in text_json])
        thresh_size = median(sizes)*1.1

        for i in range(len(text_json)):
            if text_json[i]['size'] > thresh_size:
                text_json[i]['json']['datatype'] = 'title'
        return text_json
        
    def _detect_lists(self, json_resp):
        init_chars_ul = ['•', '▪', 'o', '-']
        init_chars_ol = ['[0-9]{1,3}\\)', '[0-9]{1,3}\\.', '[0-9]{1,3}-',
                        '[a-z]{1,3}\\.', '[a-z]{1,3}\\)', '[a-z]{1,3}-',
                        '[A-Z]{1,3}\\.', '[A-Z]{1,3}\\)', '[A-Z]{1,3}-']
        is_list = re.compile('^\s*([•▪o-])|([0-9a-zA-Z]{1,3}[\\)\\.-])\s+.*')

        new_json_resp = []
        i = 0
        while i < len(json_resp):
            if json_resp[i]['datatype'] == 'text' and bool(re.match(is_list, json_resp[i]['text'])):
                # Get compiler with specific special character for list iteration
                item_complier = None
                init_char = None
                for sc in init_chars_ul + init_chars_ol:
                    sc_complier = re.compile(f'(\s*({sc}\s+)((?!(\s+{sc}\s+)).)*)')
                    if bool(re.match(sc_complier, json_resp[i]['text'])):
                        item_complier = sc_complier
                        init_char = sc
                        break

                list_items = []
                combined = False
                if item_complier is not None:
                    list_items = [l[0].strip() for l in re.findall(item_complier, json_resp[i]['text'])]
                    while i+1 < len(json_resp) and bool(re.match(item_complier, json_resp[i+1]['text'])):
                        i += 1
                        list_items = list_items + [l[0].strip() for l in re.findall(item_complier, json_resp[i]['text'])]
                        combined = True
                
                if combined or len(list_items) >= 2:
                    new_json_resp.append(self._list_to_json(list_items, tag=('ul' if init_char in init_chars_ul else 'ol')))
                else:
                    new_json_resp.append(json_resp[i])
            else:
                new_json_resp.append(json_resp[i])
            i += 1

        return new_json_resp

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
            box = [table['x0'], table['top'], table['x1'], table['bottom']]
            box[0] = max(page.bbox[0], box[0])
            box[1] = max(page.bbox[1], box[1])
            box[2] = min(page.bbox[2], box[2])
            box[3] = min(page.bbox[3], box[3])
            page = page.outside_bbox(box)
        return page
        
        