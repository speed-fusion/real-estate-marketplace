import requests
import json
from bs4 import BeautifulSoup
import os

class RedfinScraper:
    def __init__(self):
        username = os.environ.get("PROXY_USERNAME")
        password = os.environ.get("PROXY_PASSWORD")
        self.max_retry_count = 10
        self.prefix = "https://www.redfin.com"
        self.proxy = { 
           "http": f'http://{username}:{password}@gate.dc.smartproxy.com:20000',
           "https": f'http://{username}:{password}@gate.dc.smartproxy.com:20000'
        }
    
    def get_page_soup(self,url):
        payload={}
        headers = {
          'authority': 'www.redfin.com',
          'pragma': 'no-cache',
          'cache-control': 'no-cache',
          'sec-ch-ua': '"Google Chrome";v="95", "Chromium";v="95", ";Not A Brand";v="99"',
          'sec-ch-ua-mobile': '?0',
          'sec-ch-ua-platform': '"Windows"',
          'upgrade-insecure-requests': '1',
          'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36',
          'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
          'sec-fetch-site': 'none',
          'sec-fetch-mode': 'navigate',
          'sec-fetch-user': '?1',
          'sec-fetch-dest': 'document',
          'accept-language': 'en-US,en;q=0.9'}
        for retry in range(0,self.max_retry_count):
            response = requests.request("GET", url, headers=headers, data=payload,proxies=self.proxy)
            if response.status_code == 200:
                break
        print("soup status code : ",response.status_code)
        soup = BeautifulSoup(response.text)

        return soup

    
    def get_required_data(self,soup):
        buyerBrokerageName = None
        boughtWith = None
        bought_with_txt = None
        status = False
        try:
            for item in soup.find_all("div",{"data-rf-test-id":"agentInfoItem-agentDisplay"}):
                if "Bought with" in item.text:
                    bought_with_txt = item.text.strip()        

            if bought_with_txt:
                data_list = bought_with_txt.split("•")
                if len(data_list) == 2:
                    boughtWith = data_list[0].replace("Bought with","").strip()
                    buyerBrokerageName = data_list[1].strip()
                    status = True
                elif len(data_list) == 1 and "Bought with" in data_list[0]:
                    boughtWith = data_list[0].replace("Bought with","").strip()
                    status = True
        except:
            pass

        return {"boughtWith":boughtWith,"buyerBrokerageName":buyerBrokerageName,"txt":bought_with_txt,"status":status}
    def get_suggestions(self,address):
        url = f'https://www.redfin.com/stingray/do/location-autocomplete?location={address}&start=0&count=10&v=2&al=1&iss=false&ooa=true&mrs=false'

        payload={}
        headers = {
          'authority': 'www.redfin.com',
          'pragma': 'no-cache',
          'cache-control': 'no-cache',
          'sec-ch-ua': '"Google Chrome";v="95", "Chromium";v="95", ";Not A Brand";v="99"',
          'sec-ch-ua-mobile': '?0',
          'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36',
          'sec-ch-ua-platform': '"Windows"',
          'accept': '*/*',
          'sec-fetch-site': 'same-origin',
          'sec-fetch-mode': 'cors',
          'sec-fetch-dest': 'empty',
          'referer': 'https://www.redfin.com/',
          'accept-language': 'en-US,en;q=0.9'
        }
        for retry in range(0,self.max_retry_count):
            response = requests.request("GET", url, headers=headers, data=payload,proxies=self.proxy)
            if response.status_code == 200:
                break
        print("suggestion status code : ",response.status_code)
        json_text = response.text.replace("{}&&","")
        
        try:
            json_data = json.loads(json_text)
        except:
            json_data = None
        print(json_data)
        return json_data
    def get_property_url(self,json_data):
        url = None
        try:
            exactMatch = json_data["payload"]["exactMatch"]
            print(exactMatch)
            url = exactMatch["url"]
            if url != None:
                url = self.prefix + url
        except Exception as e:
            print(str(e))
        return url
            
            
            
    def get_redfin_data(self,address):
        buyerBrokerageName = None
        boughtWith = None
        bought_with_txt = None
        url = None
        status = False
        json_data = self.get_suggestions(address)
        if json_data != None:
            url =  self.get_property_url(json_data)
            if url != None:
                soup = self.get_page_soup(url)
                required_data = self.get_required_data(soup)
                buyerBrokerageName = required_data["buyerBrokerageName"]
                boughtWith = required_data["boughtWith"]
                bought_with_txt = required_data["txt"]
                status = required_data["status"]
            else:
                print("url not found")
        else:
            print("no suggestion found")
        return {
            "ok":status,
            "data":{
                "buyerBrokerageName":buyerBrokerageName,
                "boughtWith":boughtWith,
                "txt":bought_with_txt,
                "url":url,
            }
        }
                
        
        

