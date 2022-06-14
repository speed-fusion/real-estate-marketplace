import pymongo
from datetime import datetime
import requests
import urllib.parse
import os

user = os.environ.get("MONGO_USERNAME") 
password = os.environ.get("MONGO_PASSWORD")
host = "mongodb:27017"

class Database:
    def __init__(self):
        db_name = "greatschools"
        connection_uri = f'mongodb://{user}:{password}@{host}/?authSource=admin'
        client = pymongo.MongoClient(connection_uri)
        db = client[db_name]
        self.session = db["session"]
        
class GreatSchools:
    def __init__(self):
        self.db = Database()
        self.cookie = None
        self.x_csrf_token = None
        self.google_map_api_key = os.environ.get("GOOGLE_MAP_API_KEY")
        
    
    def load_session(self):
        data = list(self.db.session.find({"key":"session-data"}))[0]
        self.cookie = data["cookie"]
        self.x_csrf_token = data["x-csrf-token"]
        print(f'session data loaded : {data}')
    

    def fetch_location(self,address):
        url = f'https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={self.google_map_api_key}'

        response = requests.request("GET", url)
        
        
        temp = {}
        
        try:
            json_data = response.json()["results"][0]
            location_type = json_data["types"][0]
        except:
            location_type = None

        temp["location_type"]  = location_type

        try:
            lat_lng = json_data["geometry"]["location"]
            temp["lat"] = lat_lng["lat"]
            temp["lng"] = lat_lng["lng"]
        except:
            lat_lng = None
            temp["lat"] = None
            temp["lng"] = None


        return temp
    
    def update_session(self,data):
        temp = data.copy()
        temp["updated_at"] = datetime.now()
        self.db.session.update_one(
        {"key":"session-data"},
            {"$set":temp}
        )
        
        print(f'session data updated : {temp}')
        
    def fetch_schools(self,lat,lon,address):
        url = f'https://www.greatschools.org/gsr/api/schools?sort=rating&limit=100&level_code=p,e,m,h&lat={lat}&lon={lon}&locationType=street_address'

        payload={}
        headers = {
          'authority': 'www.greatschools.org',
          'pragma': 'no-cache',
          'cache-control': 'no-cache',
          'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="97", "Chromium";v="97"',
          'accept': 'application/json, text/javascript, */*; q=0.01',
          'x-csrf-token': self.x_csrf_token,
          'sec-ch-ua-mobile': '?0',
          'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36',
          'x-requested-with': 'XMLHttpRequest',
          'sec-ch-ua-platform': '"Windows"',
          'sec-fetch-site': 'same-origin',
          'sec-fetch-mode': 'cors',
          'sec-fetch-dest': 'empty',
          'referer': 'https://www.greatschools.org/search/search.page?gradeLevels%5B%5D=e&lat=30.0790358&locationLabel=3206%20Deer%20Valley%20Dr%2C%20Spring%2C%20TX%2077373%2C%20USA&locationType=street_address&lon=-95.3896402&st=public_charter&st=public&st=charter&state=TX',
          'accept-language': 'en-US,en;q=0.9',
          'cookie': self.cookie    
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        # cookie = response.headers.get("Set-Cookie",None)
        # if cookie != None:
        #     csrf = cookie.split(";")[0].replace("csrf_token=","")
        #     csrf = urllib.parse.unquote(csrf)
        #     self.update_session({"cookie":cookie,"x-csrf-token":csrf})
        
        json_data = response.json()

        filtered_schools = []
        print(f'total schools : {len(json_data["items"])}')
        
        temp = {
            "elementary":
                {
                    "name":"NA",
                    "rating":"NA",
                    "link":"NA"
                },
            "middle":
                {
                    "name":"NA",
                    "rating":"NA",
                    "link":"NA"
                },
            "high":
                {
                    "name":"NA",
                    "rating":"NA",
                    "link":"NA"
                },
        }
        Elementary = []
        Middle = []
        High = []
        
        try:
        
            for school in json_data["items"]:
                if school["assigned"] == True:
                    temp_ = {}
                    temp_["name"] = school["name"]
                    temp_["rating"] = school["rating"]
                    temp_["link"] = "https://www.greatschools.org" + school["links"]["profile"]
                    
                    
                    if "e" in school["levelCode"].split(","):
                        Elementary.append(temp_)
                    
                    if "m" in school["levelCode"].split(","):
                        Middle.append(temp_)
                    
                    if "h" in school["levelCode"].split(","):
                        High.append(temp_)
        except:
            pass
                    
#         print(temp)
        overall_rating = []
        
        if len(Elementary) > 0:
            temp["elementary"] = Elementary[0]
        
        if len(Middle) > 0:
            temp["middle"] = Middle[0]
        
        if len(High) > 0:
            temp["high"] = High[0]
        
        overall_rating = []
        for level in temp.keys():
            rating = temp[level]["rating"]
            if rating !=None:
                overall_rating.append(rating)
                
        try:
            temp["overall_avg_rating"] = round(sum(overall_rating)/len(overall_rating),2)
        except:
            temp["overall_avg_rating"] = "NA"
        
        temp["address"] = address
        if temp["elementary"]["link"] == "NA" and temp["middle"]["link"] == "NA" and temp["high"]["link"] == "NA":
            temp["search_url"] = "NA"
        else:
            temp["search_url"] = f'https://www.greatschools.org/search/search.page?lat={lat}&lon={lon}&locationLabel={urllib.parse.quote_plus(address)}&locationType=street_address'        
        
        return temp
    
    def fetch_data(self,address):
        self.load_session()
        lat_lon = self.fetch_location(address)
        schools = self.fetch_schools(lat_lon["lat"],lat_lon["lng"],address)
        
        return schools

if __name__ == "__main__":
    gs = GreatSchools()
    print(gs.fetch_data("3206 Deer Valley Dr, Spring, TX 77373, USA"))
