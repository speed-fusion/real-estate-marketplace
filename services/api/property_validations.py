class PropertyValidations:
    def __init__(self):
        
        self.min_bedroom = 2
        
        self.min_built = 1950
        
        self.home_types = [
            "single_family",
            "single_family_home"
        ]
        
        self.zestimate_between = {
            "min":90 * 1000,
            "max":350 * 1000
        }
        
        self.fema_flood_zone = ["X"]
        
        self.max_area_sqft = 1.5 * 43560
        
    
    def bedroom_validation(self,bedroom):
        
        if bedroom == None:
            return False, "bedroom is not available"
        
        if bedroom > self.min_bedroom:
            return True,f'bedroom({bedroom}) is more than minimum({self.min_bedroom}) bedroom'
        else:
            return False,f'bedroom({bedroom}) is less than minimum({self.min_bedroom}) bedroom'
    
    def built_validation(self,built):
        
        if built == None:
            return False,"built is not available"
        
        if built > self.min_built:
            return True, f'built({built}) is more than minimum({self.min_built}) built'
        else:
            return False,f'built({built}) is less than minimum({self.min_built}) built'
    
    def property_type_validation(self,home_type):
        
        if home_type == None:
            return False,"home type is not available"
        
        if home_type in self.home_types:
            return True,f'home type({home_type}) is available in valid ({self.home_types}) home types'
        else:
            return False,f'home type({home_type}) is not available in valid ({self.home_types}) home types'
        
    def zestimate_validation(self,zestimate):
        
        if zestimate == None:
            return False,"zestimate is not available"
        
        if zestimate >= self.zestimate_between["min"]:
            if zestimate <= self.zestimate_between["max"]:
                return True,f'zestimate({zestimate}) is more than {self.zestimate_between["min"]} and less than {self.zestimate_between["max"]}'
            else:
                return False,f'zestimate({zestimate}) is more than max({self.zestimate_between["max"]}) zestimate'
        else:
            return False,f'zestimate({zestimate}) is less than min({self.zestimate_between["min"]}) zestimate'
    
    def area_sqft_validation(self,area_sqft):
        
        if area_sqft == None:
            return False,"area sqft is not available"
        
        if area_sqft <= self.max_area_sqft:
            return True,f'area sqft({area_sqft}) is less than max({self.max_area_sqft})'
        else:
            return False,f'area sqft({area_sqft}) is more than max({self.max_area_sqft})'
    
    def fema_flood_zone_validation(self,fema_flood_zone):
        if fema_flood_zone == None:
            return False,"fema flood zone is not available"
        
        if fema_flood_zone in self.fema_flood_zone:
            return True,f'fema flood zone({fema_flood_zone}) is available in valid fema flood zones ({self.fema_flood_zone})'
        else:
            return False,f'fema flood zone({fema_flood_zone}) is not available in valid fema flood zones ({self.fema_flood_zone})'
    
    def to_int(self,value):
        try:
            return int(float(value))
        except:
            return None
    
    def apply_validation(self,data):
        failed = []
        
        bedroom = self.to_int(data["bedroom"])
        
        built = self.to_int(data["built"])
        
        property_type = data["property_type"]
        
        zestimate = self.to_int(data["zestimate"])
        
        area_sqft = self.to_int(data["area_sqft"])
        
        fema_flood_zone = data["fema_flood_zone"]
        
        status,message = self.bedroom_validation(bedroom)
        
        if status == False:
            failed.append(message)
            return False,failed
        
        status,message = self.built_validation(built)
        
        if status == False:
            failed.append(message)
            return False,failed
        
        status,message = self.property_type_validation(property_type)
        
        if status == False:
            failed.append(message)
            return False,failed
        
        status,message = self.zestimate_validation(zestimate)
        
        if status == False:
            failed.append(message)
            return False,failed
        
        status,message = self.area_sqft_validation(area_sqft)
        
        if status == False:
            failed.append(message)
            return False,failed
        
        status,message = self.fema_flood_zone_validation(fema_flood_zone)
        
        if status == False:
            failed.append(message)
            return False,failed
        
        return True,failed