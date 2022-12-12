from ParserBase import ParserBase
import os
import requests
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import sys
import json

UPLOAD_EXTENSIONS = ['.html', '.htm']

class HTMLParser(ParserBase):
    """
    HTML Parser that runs javascript and allows the page to fully load
    
    """
    
    def __init__(self, data, html_parser_url, driver_path=None):
        if os.path.exists(data):
            data = f"file:///{os.path.abspath(data)}"
        
        # Check if data is a url
        else:
            try:
                requests.get(data)
            except:
                raise "Data is not a valid file location, or a URL"
                
        self.data = data
        self.html_parser_url = html_parser_url
        self.driver_path = driver_path
        if self.driver_path is None:
            self.driver_path = "./chromedriver.exe" if sys.platform.startswith('win') else "/usr/local/bin/chromedriver"
        
        super(HTMLParser, self).__init__()
      
    def parse(self, headless=True):
        browser = self.get_browser(headless=headless)
        browser.get(self.data)

        json_resp = self._parse_iframes(browser)
        self.parsed_data = [j for j in json_resp if j['datatype'] != 'iframe']
        browser.close()
        browser.quit()
        
        return super(HTMLParser, self).parse()

    def _fix_urls(self, browser):
        # Turn all relative URLs into absolute
        for attrib in ['href', 'src']:
            for el in browser.find_elements_by_xpath(f"//*[boolean(@{attrib})]"):
                browser.execute_script(f"arguments[0].setAttribute('{attrib}','{el.get_attribute(attrib)}')", el)

    def _parse_iframes(self, browser):
        # Get content of current page
        self._fix_urls(browser)
        data = browser.page_source
        json_resp = self._parse_basic_html(data)

        iframes = browser.find_elements_by_xpath("//iframe[@src]")
        for iframe in iframes:
            # Get iframe index in json_resp
            iframe_src = iframe.get_attribute('src')
            iframe_index = [i for i, f in enumerate(json_resp) if (f['datatype'] == 'iframe') and (f['url'] == iframe_src)]
            if len(iframe_index) > 0:
                iframe_index = iframe_index[0]

                # Replace iframe object with its content
                browser.switch_to.frame(iframe)
                iframe_json_resp = self._parse_iframes(browser)
                json_resp = json_resp[:iframe_index] + iframe_json_resp + json_resp[(iframe_index+1):]
                browser.switch_to.parent_frame()

        return json_resp

    def get_browser(self, headless=True):
        userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36"

        options = Options()
        options.add_argument('--lang=en-us')
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--start-maximized")
        options.add_argument(f'--user-agent={userAgent}')

        # Remove caching 
        options.add_argument("--disable-cache")
        options.add_argument("--aggressive-cache-discard")
        options.add_argument("--disable-application-cache")
        options.add_argument("--disable-offline-load-stale-cache")
        
        # Disable GPU and Visuals
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-impl-side-painting")
        options.add_argument("--disable-gpu-sandbox")
        options.add_argument("--disable-accelerated-2d-canvas")
        if(headless):
            options.add_argument('--headless')
        
        # Do not show automation
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        browser = webdriver.Chrome(executable_path=self.driver_path, options=options)
        return browser

    def _parse_basic_html(self, html):
        json_resp = {}
        try:
            json_resp = requests.post(self.html_parser_url, data={'data': html, 'include_iframe': True})
            json_resp = json_resp.json()
        except:
            raise "Basic HTML Parser not responding"
        
        self.urls = self.urls + json_resp['urls']
        return json_resp['data']