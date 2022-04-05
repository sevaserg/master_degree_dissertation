from rdflib import Graph
from tabulate import tabulate
import pymorphy2
import json
import sys
from speechRecog import speech_recog as sr
g = Graph()
devices_json_path = ""

prefixes = '''PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX iot: <http://voice.iot#>
'''

def search_query(name):
    q =  prefixes + '''SELECT * WHERE {
        ?subject ?predicate ?object .
        ?object rdfs:label "''' + name + '''"@ru .
        ?object rdfs:label ?lbl .
        ?subject a ?cls .
        }
        '''
    return g.query(q)

def search_all():
    q =  prefixes + '''SELECT * WHERE {
        ?subject ?predicate ?object .
        ?object rdfs:label ?lbl .
        ?subject a ?cls .
        }
        '''
    return g.query(q)

def tokenize_and_lemmatize(sentence):
    data = []
    for word in sentence.split(" "):
        try:
            data.append(morph.parse(word)[0].normal_form)
        except:
            data.append(word)
    return data

class nl_query:
    def __init__(self, sentence):
        self.system         = "none"
        self.commandProto   = "none"
        self.params          = []

        tokenized_sentence  = tokenize_and_lemmatize(sentence)
        for word in tokenized_sentence:
            data_to_parse   = search_query(word)
            for entry in data_to_parse:
                if str(entry.cls) == "http://purl.oclc.org/NET/ssnx/ssn#System":
                    self.system = str(entry.subject)
                if str(entry.cls) == "http://voice.iot/PrototypeCommand":
                    self.commandProto = str(entry.subject)

    def print(self):
        print("System:", self.system)
        print("CommandProto:", self.commandProto)
        print("Params:")
        for param in self.params:
            print(param)
    
    def execute(self):
        f = open(devices_json_path, "r")
        devices = json.loads(f.read())
        f.close()
        system_q = ""
        ip_q = ""
        func_q   = ""
        should_find_query = (self.system == "none")
        for device in devices["devices"]:
            if device["KB_ID"] == self.system:
                should_find_query = True
            if should_find_query:
                for q in device["queries"]:
                    if q["KB_ID"] == self.commandProto:
                        system_q = device["system"]
                        func_q = q["name"]
                        ip_q = device["ip"]
                        break
        if ip_q != "":
            print(f"{system_q} ({ip_q}) - {func_q}")

if __name__ == "__main__":
    f           = open ('config.json', "r")
    config      = json.loads(f.read())
    model_path  = ""
    kb_path     = ""
    try:
        devices_json_path = config["devices_path"]
    except:
        raise Exception("No \"devices\" path in config.json!")
    try:
        kb_path = config["kb_path"]
        f.close()
    except:
        raise Exception("No \"knowledge base\" path in config.json!")
    try:
        f = open (devices_json_path, "r")
        f.close()
    except:
        raise Exception ("Devices file \""+devices_json_path+"\" does not exist! Check if path in config.json is correct.")
    try:
        f = open (kb_path, "r")
        f.close()
    except:
        raise Exception ("Knowledge base file \""+kb_path+"\" does not exist! Check if path in config.json is correct.")
    try:
        f = open (kb_path, "r")
        f.close()
    except:
        raise Exception ("Knowledge base file \""+kb_path+"\" does not exist! Check if path in config.json is correct.")

    g.parse(kb_path)
    
    morph = pymorphy2.MorphAnalyzer(lang='ru')
    speech_recognition = sr()
    ################################################
    while True:
        pass
    ################################################
    data = nl_query(sys.argv[1])
    data.execute()
