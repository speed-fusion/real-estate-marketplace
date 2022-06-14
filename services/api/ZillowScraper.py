import requests
import os
class ZillowScraper:
    def __init__(self):
        username = os.environ.get("PROXY_USERNAME")
        password = os.environ.get("PROXY_PASSWORD")
        
        self.max_retry_count = 3
        
        self.proxy = { 
           "http": f'http://{username}:{password}@gate.dc.smartproxy.com:20000',
           "https": f'http://{username}:{password}@gate.dc.smartproxy.com:20000'
        }
        
        self.suggestion_url = "https://www.zillowstatic.com/autocomplete/v3/suggestions?q={}"
        
    def get_suggestions(self,address):
        headers = {
          'authority': 'www.zillowstatic.com',
          'pragma': 'no-cache',
          'cache-control': 'no-cache',
          'sec-ch-ua': '"Chromium";v="94", "Google Chrome";v="94", ";Not A Brand";v="99"',
          'sec-ch-ua-mobile': '?0',
          'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
          'sec-ch-ua-platform': '"Windows"',
          'accept': '*/*',
          'origin': 'https://www.zillow.com',
          'sec-fetch-site': 'cross-site',
          'sec-fetch-mode': 'cors',
          'sec-fetch-dest': 'empty',
          'accept-language': 'en-US,en;q=0.9'
        }
        
        response = requests.request("GET", self.suggestion_url.format(address), headers=headers,proxies=self.proxy)
        
        return response.json()
    
    def get_data_by_zpid(self,zillow_property_id):
        url = 'https://www.zillow.com/graphql/?zpid='+zillow_property_id+'&contactFormRenderParameter=&queryId=d64cbbc1458567321829e9cf1283438c&operationName=ForRentDoubleScrollFullRenderQuery'

        payload = '{"operationName":"ForRentDoubleScrollFullRenderQuery","variables":{"zpid":'+zillow_property_id+',"contactFormRenderParameter":{"zpid":'+zillow_property_id+',"platform":"desktop","isDoubleScroll":true}},"clientVersion":"home-details/6.0.11.6224.master.d2a245b","queryId":"d64cbbc1458567321829e9cf1283438c"}'
        headers = {
          'authority': 'www.zillow.com',
          'sec-ch-ua': '"Chromium";v="94", "Google Chrome";v="94", ";Not A Brand";v="99"',
          'sec-ch-ua-mobile': '?0',
          'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
          'sec-ch-ua-platform': '"Windows"',
          'content-type': 'text/plain',
          'accept': '*/*',
          'origin': 'https://www.zillow.com',
          'sec-fetch-site': 'same-origin',
          'sec-fetch-mode': 'cors',
          'sec-fetch-dest': 'empty',
          'referer': 'https://www.zillow.com/homedetails/1075-United-Ave-SE-Atlanta-GA-30316/35828919_zpid/',
          'accept-language': 'en-US,en;q=0.9'
        }

        response = requests.request("POST", url, headers=headers, data=payload,proxies=self.proxy)

        return response.json()
    
    def get_property_info(self,address):
        zpid = None
        status = False
        message = None
        resp_data = {}
        try:
            suggestions = self.get_suggestions(address)
            results = suggestions["results"]
            if len(results) > 0:
                zpid = str(results[0]["metaData"]["zpid"])
            else:
                message = "address not found on zillow."
        except:
            message = "address not found on zillow."
        
        if zpid != None:
            try:
                property_info = self.get_data_by_zpid(zpid)
                try:
                    bought_with = property_info["data"]["property"]["attributionInfo"]["buyerAgentName"]
                except:
                    bought_with = None
                try:
                    buyerBrokerageName = property_info["data"]["property"]["attributionInfo"]["buyerBrokerageName"]
                except:
                    buyerBrokerageName = None
                try:
                    zestimate = property_info["data"]["property"]["zestimate"]
                except:
                    zestimate = None
                try:
                    rentZestimate = property_info["data"]["property"]["rentZestimate"]
                except:
                    rentZestimate = None
                status = True
                resp_data["boughtWith"] = bought_with
                resp_data["buyerBrokerageName"] = buyerBrokerageName
                resp_data["zestimate"] = zestimate
                resp_data["rentZestimate"] = rentZestimate
                resp_data["zpid"] = zpid
                message = "OK"
            except Exception as e:
                print(str(e))
                message = "address found on zillow but property info is not available."
        return {
            "status":status,
            "data":resp_data,
            "msg":message
        }
    
    def get_zillow_data(self,address):
        zillow_resp = None
        for retry in range(0,self.max_retry_count):
            zillow_resp = self.get_property_info(address)
            if zillow_resp["status"] == True:
                break
        return zillow_resp
    
            

