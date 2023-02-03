from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename
import os
from Parser import *

app = Flask(__name__)							
app.config['UPLOAD_FOLDER'] = 'files/'
app.config['UPLOAD_EXTENSIONS'] = UPLOAD_EXTENSIONS

# Use the same browser for ever parsing call.
browser = None

@app.route('/parse', methods=['POST'])
def parse():
    add_images = bool(request.form.get('add_images', request.files.get('add_images', False)))

    global browser
    if request.method == 'POST' and ('data' in request.files):
        data = request.files['data']
        filename = secure_filename(data.filename)
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                return jsonify({'error': "File extension not allowed"}), 401
            
            filename = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            data.save(filename)
            parser = HTMLParser(filename, browser=browser, html_parser_url='http://basichtmlparser:8000/parse')
            json_resp = jsonify(parser.parse(add_images=add_images))
            browser = parser.browser
            return json_resp

    if request.method == 'POST' and ('data' in request.form):
        data = request.form['data']
        parser = HTMLParser(data, browser=browser, html_parser_url='http://basichtmlparser:8000/parse')
        json_resp = jsonify(parser.parse(add_images=add_images))
        browser = parser.browser
        return json_resp

    return jsonify({'error': "Data is missing"}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)