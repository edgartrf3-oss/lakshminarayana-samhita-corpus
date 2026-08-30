from __future__ import annotations
import random,time,requests
RETRYABLE_STATUS={429,500,502,503,504}
class MediaWikiClient:
    def __init__(self,endpoint,user_agent,delay=.5,max_retries=8,maxlag=5):
        self.endpoint=endpoint; self.delay=delay; self.max_retries=max_retries; self.maxlag=maxlag
        self.session=requests.Session(); self.session.headers.update({"User-Agent":user_agent,"Api-User-Agent":user_agent})
    def get(self,params):
        p={"format":"json","formatversion":"2","maxlag":self.maxlag,**params}
        for attempt in range(self.max_retries+1):
            try:
                r=self.session.get(self.endpoint,params=p,timeout=120)
                if r.status_code in RETRYABLE_STATUS:
                    ra=r.headers.get("Retry-After"); time.sleep(float(ra) if ra and ra.isdigit() else min(60,2**attempt+random.random())); continue
                r.raise_for_status(); data=r.json(); err=data.get("error") if isinstance(data,dict) else None
                if err and err.get("code")=="maxlag": time.sleep(min(60,max(2,float(err.get("lag",5))))); continue
                if self.delay>0: time.sleep(self.delay)
                return data
            except (requests.RequestException,ValueError):
                if attempt>=self.max_retries: raise
                time.sleep(min(60,2**attempt+random.random()))
        raise RuntimeError("MediaWiki request failed")
    def allpages(self,prefix,namespace=0):
        cont={}
        while True:
            data=self.get({"action":"query","list":"allpages","apprefix":prefix,"apnamespace":namespace,"aplimit":"max",**cont})
            yield from data.get("query",{}).get("allpages",[])
            if "continue" not in data: break
            cont=data["continue"]
    def revisions_with_content_by_pageid(self,pageids,batch_size=25):
        out=[]
        for i in range(0,len(pageids),batch_size):
            data=self.get({"action":"query","prop":"revisions","pageids":"|".join(map(str,pageids[i:i+batch_size])),"rvprop":"ids|timestamp|sha1|size|content","rvslots":"main"})
            out.extend(data.get("query",{}).get("pages",[]))
        return out
