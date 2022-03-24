from rdflib import Graph
from tabulate import tabulate
prefixes = '''PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX iot: <http://voice.iot#>
'''

def search_query(name):
    q =  prefixes + '''SELECT * WHERE { ?subject ?predicate ?object .
            ?object rdfs:label "''' + name + '''"@ru .
            ?subject a ?cls .
            
            ?object rdfs:label ?lbl .
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


g = Graph()

g.parse("./iot_model.ttl")
test = []
for data in search_all(): # search_query("люмен"):
    #print(data.subject, data.object, data.lbl, data.cls)
    test.append([data.subject, data.object, data.lbl, data.cls])


col_names = ["Item URI", "Label URI", "Label", "Class"]

print(tabulate(test, headers=col_names))