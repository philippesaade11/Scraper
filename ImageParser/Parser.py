import sys
sys.path.append('ml')
from ml.models import *
import warnings

warnings.filterwarnings("ignore")

from ParserBase import ParserBase
import os
import requests
import uuid
import time

UPLOAD_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.webp', '.JPG', '.PNG', '.JPEG']

class ImageParser(ParserBase):
    """
    Image Parser
    
    """
    parser_name = 'imageparser'
    
    def __init__(self, data, ocr_model=None, detector_model=None):
        if not os.path.exists(data):
            try:
                image = Image.open(requests.get(data, stream=True).raw)
                data = f'files/{str(uuid.uuid4())}.jpg'
                image.save(data)
            except:
                raise Exception("Image not found")

        self.data = data
        start = time.time()
        self.ocr_model = ocr_model if ocr_model is not None else get_ocr_model()
        with open('benchmark.csv', 'a+') as f:
            f.write(f'prepare ocr model,{start},{time.time()},{self.data}\n')

        start = time.time()
        self.detector_model = detector_model if detector_model is not None else get_detector_model()
        with open('benchmark.csv', 'a+') as f:
            f.write(f'prepare detector model,{start},{time.time()},{self.data}\n')
        super(ImageParser, self).__init__()
        
    def parse(self):
        ocr_output = get_ocr_output(self.ocr_model, self.data)
        detector_output = get_detector_output(self.detector_model, self.data)

        detector_output['classes'], detector_output['boxes'] = zip(*sorted(zip(detector_output['classes'], detector_output['boxes']), key=self._sort_key_function))
        json_resp = self._combine_detector_ocr(detector_output, ocr_output)
        self.parsed_data = json_resp
        return super(ImageParser, self).parse()

    def _sort_key_function(self, x):
        top = round(int(x[1][1])/50)*50
        left = int(x[1][0])
        return top*10000 + left

    def _combine_detector_ocr(self, detector_output, ocr_output):
        json_resp = []
        for cls, box in zip(detector_output['classes'], detector_output['boxes']):
            if cls == 0:
                text = self._extract_text_in_box(box, ocr_output)
                if text != '':
                    json_resp.append(self._text_to_json(text))
            elif cls == 1:
                title = self._extract_text_in_box(box, ocr_output)
                if title != '':
                    json_resp.append(self._title_to_json(title))

        return json_resp

    def _extract_text_in_box(self, box, ocr_output):
        text = ''
        for block in ocr_output['pages'][0]['blocks']:
            if self._rectangles_overlap(box, block['geometry'], ocr_output['pages'][0]['dimensions']):
                if text != '':
                    text += '\n'
                for line in block['lines']:
                    text += ' '.join([w['value'] for w in line['words']])+' '
        return text.strip()

    def _rectangles_overlap(self, detector_box, ocr_box, page_dim):
        detector_x1, detector_y1, detector_x2, detector_y2 = detector_box
        (ocr_x1, ocr_y1), (ocr_x2, ocr_y2) = ocr_box
        ocr_x1 = ocr_x1*page_dim[1]
        ocr_x2 = ocr_x2*page_dim[1]
        ocr_y1 = ocr_y1*page_dim[0]
        ocr_y2 = ocr_y2*page_dim[0]

        assert ocr_x1 < ocr_x2
        assert ocr_y1 < ocr_y2
        assert detector_x1 < detector_x2
        assert detector_y1 < detector_y2

        x_left = max(detector_x1, ocr_x1)
        y_top = max(detector_y1, ocr_y1)
        x_right = min(detector_x2, ocr_x2)
        y_bottom = min(detector_y2, ocr_y2)

        if x_right < x_left or y_bottom < y_top:
            return False

        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        ocr_box_area = (ocr_x2 - ocr_x1) * (ocr_y2 - ocr_y1)
        # If more than half of the OCR box is inside the Detector box then the word is included
        return (intersection_area / ocr_box_area) > 0.5
