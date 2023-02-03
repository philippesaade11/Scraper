from flask import Flask, jsonify, request, send_file
from werkzeug.utils import secure_filename
from mimetypes import guess_extension
from crawler import Crawler
import os
import requests
import json
import io

config = {}
with open("config.json") as outfile:
    config = json.load(outfile)

main_app = Flask(__name__)							
main_app.config['UPLOAD_FOLDER'] = 'files/'

@main_app.route('/parse', methods=['POST'])
def parse():
    url_regex = request.form.get('url_regex', request.files.get('url_regex', '.*'))
    max_depth = max(1, int(request.form.get('max_depth', request.files.get('max_depth', 1))))
    parse_images = bool(request.form.get('parse_images', request.files.get('parse_images', False)))

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
        crawler = Crawler(filename, config['parsers'], url_regex=url_regex, max_depth=max_depth, parse_images=parse_images)
        resp = crawler.parse()
        return jsonify(resp)

    return jsonify({'error': "Data is missing"}), 401

@main_app.route('/getimage/<file_name>', methods=['GET'])
def getimage(file_name):
    parser_name = request.args.get('parser', request.form.get('parser'))
    for parser in config['parsers']:
        if parser_name == parser['name']:
            r = requests.get(f'http://{parser["name"]}:{parser["port"]}/static/{file_name}')
            return send_file(io.BytesIO(r.content), mimetype=r.headers['content-type'])
    
    return jsonify({'error': "Parser is missing"}), 401

if __name__ == '__main__':
    main_app.run(debug=True, host='0.0.0.0', port=5000)