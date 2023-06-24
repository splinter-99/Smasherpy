import logging
"""
TODO:
1. Add handling when tunnel service goes down to by adding False value for that key:value pair
"""


class TunnelServiceHandler:

    def __init__(self, urls):
        self.urls = urls
        self.tunneling_service = None
        self.urls_mapping = {key: False for key in self.urls}

    def set_tunneling_service(self):
        for key in self.urls_mapping.keys():
            if not self.urls_mapping[key]: 
                self.tunneling_service = key 
                return self.tunneling_service
        raise Exception

    def cycle_next(self):
        self.urls_mapping[self.tunneling_service] = True
        return self.set_tunneling_service()



