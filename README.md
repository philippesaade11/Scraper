# Dynamic Data Parsing System
The goal of the project is to design and implement a software that is capable of parsing data from a variety of file types, extracting relevant textual data, and combining them in one standardized format. The software is therefore used to make unstructured file formats more comprehensible and universal. The types of files include Web pages, Word documents, PDF files, RSS feeds, and Images.

## Architecture
The program is divided into multiple microservices, one service for each file parser, and one main service that acts as an intermediate between the client and the parsers.
Each microservice runs on a separate Docker container, represented with a unique folder in the repository. Each folder has the following structure:

| File name | Description |
| :--- | :--- |
| files/ | Folder to download and prepare files that need to be parsed. |
| static/ | Folder to store downloaded images. |
| app.py | Flask app that handles HTTP requests. |
| requirements.txt | Contains the necessary Python packages. |
| Dockerfile | To run the Docker container, download all required dependencies, and execute app.py |
| ParserBase.py | **Only for the parser services**, contains the abstract class. The same copy is found in all parsers. |
| Parser.py | **Only for the parser services**, extends ParserBase and runs all functions to parse the particular file type. |
| crawler.py | **Only for the main service**, contains functions to run the crawler, stores all URLs found in parsed files, recursively send each URL to the corresponding parser, and combines all results. |
| config.json | **Only for the main service**, contains JSON list of all parser with additional information required for the crawler. |

## How to use?
To build all the Docker container together, run the following command:
> docker compose up --build

The main script runs on localhost with port 5000, run the following cURL to test the parser:
> curl --location --request POST 'localhost:5000/parse' \
>--form 'data="[URL]"' \
>--form 'url_regex="[Regex]"' \
>--form 'max_depth="[Max Depth]"'

Here's a list of the form arguments the parser can handle:
| Key | Value |
| :--- | :--- |
| data | The URL or file location of the file you aim to parse |
| url_regex | Regular expression specifying which URL you would like the crawler to parse (Default: .*) |
| max_depth | The maximum depth we want the crawler to reach (Default: 1) |

## How to add a new parser?
Here are the steps you need to follow to add a new parser:
- Copy the DummyParser folder and rename it [Parser name]
- In *[Parser name]/Parser.py* change the name of the class if desired, and change the *parser_name* varible to [parsername] preferably all lowercase. Additionally, change *UPLOAD_EXTENSIONS* and include file extensions that the parser can handle.
- In *[Parser name]/app.py* change the name of the Parser class to the new one
- In *main/config.json* add the new parser to inform the crawler. Include the *name* key, copy from the new *parser_name* in the *[Parser name]/Parser.py* file, and the *file_extensions* copy from the *UPLOAD_EXTENSIONS* variable.
- In *docker-compose.yml* add the new parser, also use the same parser name as in *[Parser name]/Parser.py* and add the build directory *./[Parser name]*
