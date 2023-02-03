from ParserBase import ParserBase

UPLOAD_EXTENSIONS = ['.something']

class DummyParser(ParserBase):
    """
    Dummy Parser
    
    """
    parser_name = 'dummyparser'
    
    def __init__(self, data):
        super(DummyParser, self).__init__()
        
    def parse(self, add_images=False):
        '''
        Populate self.urls and self.parsed_data 

        '''
        return super(DummyParser, self).parse(add_files=add_images)