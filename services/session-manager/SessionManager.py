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

class SessionManager:
    def __init__(self):
        print("Session Manager")
        self.db = Database()
        self.cookie = None
        self.x_csrf_token = None
        self.load_session()
        
    
    def load_session(self):
        data = list(self.db.session.find({"key":"session-data"}))[0]
        self.cookie = data["cookie"]
        self.x_csrf_token = data["x-csrf-token"]
        print(f'session data loaded : {data}')
    
    def update_session(self,data):
        temp = data.copy()
        temp["updated_at"] = datetime.now()
        self.db.session.update_one(
        {"key":"session-data"},
            {"$set":temp}
        )
        
        print(f'session data updated : {temp}')
        
    
    
    def get_session_cookie(self):
        url = "https://www.greatschools.org/gsr/api/schools?city=&district=&state=TX&sort=rating&limit=25&url=%2Fgsr%2Fapi%2Fschools&csaYears=&level_code=e&type=public%2Ccharter&lat=30.0790358&lon=-95.3896402&extras=students_per_teacher%2Creview_summary%2Csaved_schools&locationLabel=3206+Deer+Valley+Dr%2C+Spring%2C+TX+77373%2C+USA&locationType=street_address"
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
        'Cookie': self.cookie
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        cookie = response.headers.get("Set-Cookie",None)
        
        return cookie
        
    
    

if __name__ == "__main__":
    sm = SessionManager()
    cookie = sm.get_session_cookie()
    if cookie != None:
        csrf = cookie.split(";")[0].replace("csrf_token=","")
        csrf = urllib.parse.unquote(csrf)
        sm.update_session({"cookie":cookie,"x-csrf-token":csrf})