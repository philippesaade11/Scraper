from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename
from mimetypes import guess_extension
import os
import requests
import json

config = {}
with open("config.json") as outfile:
    config = json.load(outfile)

main_app = Flask(__name__)							
main_app.config['UPLOAD_FOLDER'] = 'files/'

@main_app.route('/parse', methods=['POST'])
def parse():
    filename = None
    file_ext = None

    if request.method == 'POST' and ('data' in request.files):
        data = request.files['data']
        filename = secure_filename(data.filename)
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            filename = os.path.join(main_app.config['UPLOAD_FOLDER'], filename)
            data.save(filename)

    if request.method == 'POST' and ('data' in request.form):
        try:
            filename = request.form['data']
            r = requests.get(filename)
        except:
            return jsonify({'error': "Data is not a valid URL"}), 401

        file_ext = guess_extension(r.headers["content-type"].split(";")[0])

    if (filename is not None) and (file_ext is not None):
        for parser in config['parsers']:
            if file_ext in parser['file_extensions']:
                if os.path.exists(filename):
                    r = requests.post(f'http://{parser["name"]}:{parser["port"]}/parse', files = {'data': open(filename, "rb")})
                else:
                    r = requests.post(f'http://{parser["name"]}:{parser["port"]}/parse', data = {'data': filename})
                return jsonify(r.json())

        return jsonify({'error': "File extension not parsable"}), 401

    return jsonify({'error': "Data is missing"}), 401

if __name__ == '__main__':
    main_app.run(debug=True, host='0.0.0.0', port=5000)