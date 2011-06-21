import http.client
import urllib.parse
import email.utils
import io
import json

from . import error

def quote(string):
    return urllib.parse.quote(string, safe='')


class Server(object):
    def __init__(self, address="127.0.0.1", port=5984):
        self.address = address
        self.port = port

    def requesthttp(self, method, url, body=None, headers={}):
        conn = http.client.HTTPConnection(self.address, self.port)
        headers["Date"] = email.utils.formatdate(usegmt=True)
        conn.request(method, url, body, headers)
        resp = conn.getresponse()
        body = io.TextIOWrapper(resp, "utf-8")
        try:
            if resp.status == 400:
                raise error.BadRequest(body)
            if resp.status == 404:
                raise error.NotFound(body)
            if resp.status == 405:
                raise error.ResourceNotAllowed(body)
            if resp.status == 409:
                raise error.Conflict(body)
            if resp.status == 412:
                raise error.PreconditionFailed(body)
            if resp.status == 500:
                raise error.InternalServerError(body)
        except:
            conn.close()
            raise
        return conn, resp, body
    
    def simplehttp(self, method, url, body=None, headers={}):
        conn, resp, body = self.requesthttp(method, url, body, headers)
        conn.close()

    def getjson(self, url):
        conn, resp, body = self.requesthttp("GET", url)
        data = json.load(body)
        conn.close()
        return data

    def dblist(self):
        return [Database(self, x) for x in self.getjson("/_all_dbs")]

    def info(self):
        data = self.getjson("/")
        return data["couchdb"], data["version"]
    
    def stats(self):
        return self.getjson("/_stats")
    
    def __getitem__(self, dbname):
        return Database(self, dbname)

class Database(object):
    def __init__(self, client, name):
        if len(name) == 0:
            raise ValueError("Empty database name")
        self.server = client
        self.name = name
    
    def geturl(self):
        return "/" + quote(self.name) + "/"

    def create(self):
        self.server.simplehttp("PUT", self.geturl())
    
    def delete(self, name):
        self.server.simplehttp("DELETE", self.geturl())
    
    def info(self, name):
        return self.server.getjson(self.geturl())

    def __getitem__(self, docid):
        return Document(self, docid)

class Document(object):
    def __init__(self, database, id_ = None):
        self.database = database
        self.server = database.server
        self.id = id_
        self.ref = None
        self.data = None
    
    def geturl(self):
        return self.database.geturl() + quote(self.id) + "/"

    def refresh(self):
        return self.server.getjson(self.geturl())
    
    def getrev(self):
        conn, resp, body = self.server.requesthttp("HEAD", self.geturl())
        rev = resp.getheader("Etag")
        conn.close()

        if rev == None:
            raise error.InvalidResponse()

        return rev
    
    def delete(self, rev=None):
        if rev == None:
            rev = self.getrev()
        self.server.simplehttp("DELETE", self.geturl(), headers={"If-Match": rev})
    
    def save(self, data):
        if(self.id == None):
            self.id
        
