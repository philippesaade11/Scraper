from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename
import os
from Parser import *

app = Flask(__name__)							
app.config['UPLOAD_FOLDER'] = 'files/'
app.config['UPLOAD_EXTENSIONS'] = UPLOAD_EXTENSIONS

ocr_model = None
detector_model = None

@app.route('/parse', methods=['POST'])
def parse():
    global ocr_model
    global detector_model

    if request.method == 'POST' and ('data' in request.files):
        data = request.files['data']
        filename = secure_filename(data.filename)
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                return jsonify({'error': "File extension not allowed"}), 401
            
            filename = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            data.save(filename)
            parser = ImageParser(filename, ocr_model=ocr_model, detector_model=detector_model)
            ocr_model = parser.ocr_model
            detector_model = parser.detector_model
            return jsonify(parser.parse())

    if request.method == 'POST' and ('data' in request.form):
        data = request.form['data']
        parser = ImageParser(data, ocr_model=ocr_model, detector_model=detector_model)
        ocr_model = parser.ocr_model
        detector_model = parser.detector_model
        return jsonify(parser.parse())

    return jsonify({'error': "Data is missing"}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)