from rdflib import Graph
import pymorphy2
import json
import sys
from vosk import Model, KaldiRecognizer
import os
import pyaudio
import enum
import requests

import time

morph = pymorphy2.MorphAnalyzer(lang='ru')

def current_milli_time():
    return round(time.time() * 1000)

current_time = current_milli_time()

g = Graph()

iot     = "http://www.semanticweb.org/svg/ontologies/2022/4/untitled-ontology-4#"
class Prefix(enum.Enum):
    rdf     = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    owl     = "http://www.w3.org/2002/07/owl#"
    rdfs    = "http://www.w3.org/2000/01/rdf-schema#"
    xsd     = "http://www.w3.org/2001/XMLSchema#"
    iot     = "http://www.semanticweb.org/svg/ontologies/2022/4/untitled-ontology-4#"

def sparql(query, dbg = False):
    q =  f'''
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl: <http://www.w3.org/2002/07/owl>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX iot: <http://www.semanticweb.org/svg/ontologies/2022/4/untitled-ontology-4#>
SELECT * WHERE {{
    {query}
}}
    '''
    if dbg:
        print(q)
    return g.query(q)

def tokenize_and_lemmatize(sentence):
    data = []
    current_time = current_milli_time()
    for word in sentence.split(" "):
        try:
            data.append(morph.parse(word)[0].normal_form)
        except:
            data.append(word)
    print("Lemmatized:", end=" ")
    for word in data:
        print(word, end = " ")
    print("| took", str(current_milli_time() - current_time), "milliseconds.")
    return data

class nl_query:
    def __init__(self, sentence):
        self.can_be_executed = True
        self.systems         = []
        self.command         = ""
        self.property        = ""
        self.location        = "{iot}here"
        self.needs_property = True
        tokenized_sentence  = tokenize_and_lemmatize(sentence)
        print(tokenized_sentence)
        for word in tokenized_sentence:
            data_to_parse   = sparql(f'''?obj rdfs:label "{word}" .
    ?obj a ?cls''')
            for entry in data_to_parse:
                if str(entry.cls) == str(iot)+"System":
                    self.systems.append(str(entry.obj))
                    print("SYSTEM ADDED,", self.systems[0])
                if str(entry.cls) == str(iot)+"Command":
                    self.command = str(entry.obj)
                    for needs_prop in sparql(f'iot:{self.command.split("#")[1]} iot:needsProperty ?needs_prop'):
                        if needs_prop.needs_prop.find("true") == -1:
                            self.needs_property = False
                    print("CMD ADDED, ", self.command)
                if str(entry.cls) == str(iot)+"Property":
                    self.property = str(entry.obj)
                    print("PROPERTY ADDED, ", self.property)
                if str(entry.cls) == str(iot)+"Location":
                    self.location = str(entry.obj)
                    print("LOCATION ADDED, ", self.location)
        if len(self.systems) == 0 and self.property != "":
            for system in sparql(f'?obj iot:hasProperty iot:{self.property.split("#")[1]}'):
                self.systems.append(system.obj)
        if self.command == "":
            if self.property != "":
                for command in sparql(f'iot:{self.property.split("#")[1]} iot:defaultCommand ?cmd'):
                    self.command = command.cmd
                for needs_prop in sparql(f'iot:{self.command.split("#")[1]} iot:needsProperty ?needs_prop'):
                    if needs_prop.needs_prop.find("true") == -1:
                        self.needs_property = False
                    else:
                        if self.command == "":
                            for cmd in sparql(f'iot:{self.property.split("#")[1]} iot:defaultCommand ?cmd'):
                                self.command = cmd.cmd

            if self.property == "" and len(self.systems) != 0 and self.needs_property == True:
                for prop in sparql(f"iot:{self.systems[0].split('#')[1]} iot:defaultProperty ?prop", True):
                    self.property = prop.prop
        if self.command == "" and (self.property == "" and self.needs_property) and len(self.systems) == 0:
            self.can_be_executed = False

    def print(self):
        print("Systems: ", end = "")
        for system in self.systems:
            print(system.split(iot)[1], end = ", ")
        print()
        if self.command != "":
            print("Command: ", self.command.split(iot)[1])
        print("Needs property:", self.needs_property)
        if self.property != "" and self.needs_property:
            print("Property:", self.property.split(iot)[1])
        print("Can be executed:", self.can_be_executed)


    def execute(self):
        current_time = current_milli_time()
        if self.can_be_executed:
            for system in self.systems:
                url = "http://"
                for ip in sparql(f"iot:{system.split(iot)[1]} iot:IP ?ip"):
                    url += ip.ip+"/"
                for query in sparql(f"iot:{self.command.split(iot)[1]} iot:Query ?query"):
                    url += query.query
                if self.needs_property:
                    for query in sparql(f"iot:{self.property.split(iot)[1]} iot:Query ?query"):
                        url += "+" + query.query
                print("request sent:", url, "| took", str(current_milli_time() - current_time), "milliseconds.")

                current_time = current_milli_time()
                try:
                    x = requests.post(url)

                    print("Got the answer:", x.text, "| took", str(current_milli_time() - current_time), "milliseconds.")
                except:
                    print("Error getting the answer:", x.text, "| took", str(current_milli_time() - current_time), "milliseconds.")

            print(f"Total system status: {system_q} ({ip_q}) - {func_q}")


class QueryRecognizer:
    def __init__(self, model_name):
        model = Model(model_name)
        self.rec = KaldiRecognizer(model, 44100)
        p = pyaudio.PyAudio()
        self.stream = p.open(
            format=pyaudio.paInt16, 
            channels=1, 
            rate=44100, 
            input=True, 
            frames_per_buffer=4000
        )
    def recognize(self):
        while True:
            __data = self.stream.read(4000, exception_on_overflow = False)
            if self.rec.AcceptWaveform(__data):
                return self.rec.Result()


if __name__ == "__main__":
    f           = open ('config.json', "r")
    config      = json.loads(f.read())
    model_path  = ""
    kb_path     = ""
    try:
        kb_path = config["kb_path"]
        f.close()
    except:
        raise Exception("No \"knowledge base\" path in config.json!")
    try:
        f = open (kb_path, "r")
        f.close()
    except:
        raise Exception ("Knowledge base file \""+kb_path+"\" does not exist! Check if path in config.json is correct.")
    try:
        model_path = config["language_model_path"]
        f.close()
    except:
        raise Exception("No \"language model\" path in config.json!")
        '''
    try:
        f = open (model_path, "r")
        f.close()
    except:
        raise Exception ("Language model file \""+model_path+"\" does not exist! Check if path in config.json is correct.")
'''
    g.parse(kb_path)
    if len(sys.argv) == 1:
        morph = pymorphy2.MorphAnalyzer(lang='ru')
        qr = QueryRecognizer(r"./vosk-model-small-ru-0.22")
        while True:
            current_time = current_milli_time()
            rec_data = json.loads(qr.recognize())["text"] # pass
            if rec_data != "":
                print("Recognized: ",rec_data, "| took", str(current_milli_time()-current_time), "milliseconds.")
                query_data = nl_query(rec_data)
                query_data.execute()
    else:
        data = nl_query(sys.argv[1])
        data.print()
