from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename
import os
from Parser import *

app = Flask(__name__)							
app.config['UPLOAD_FOLDER'] = 'files/'
app.config['UPLOAD_EXTENSIONS'] = UPLOAD_EXTENSIONS

@app.route('/parse', methods=['POST'])
def parse():
    include_iframe = request.form.get('data', request.files.get('data', False))
    
    if request.method == 'POST' and ('data' in request.files):
        data = request.files['data']
        filename = secure_filename(data.filename)
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                return jsonify({'error': "File extension not allowed"}), 401
            
            parser = BasicHTMLParser(data.read())
            return jsonify(parser.parse(include_iframe=include_iframe))

    elif request.method == 'POST' and ('data' in request.form):
        data = request.form['data']
        parser = BasicHTMLParser(data)
        return jsonify(parser.parse(include_iframe=include_iframe))
        
    return jsonify({'error': "Data is missing"}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)