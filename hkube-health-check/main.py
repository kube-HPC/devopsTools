import os
import subprocess
import json
from flask import jsonify
from flask import Flask

app = Flask(__name__)
TOKEN=os.popen('cat /var/run/secrets/kubernetes.io/serviceaccount/token').read()
masterUrl= os.getenv('MASTER_CLUSTER_IP')
@app.route("/health")
def health():
    fullDic={}
    s=os.system('curl -X GET '+masterUrl+'/api/v1/namespaces/default/pods/ --header "Authorization: Bearer '+TOKEN+'" --insecure | jq . > all-pods.json')
    with open('all-pods.json', 'r') as jsonfile:
        allPods = json.load(jsonfile)
    newDic=allPods['items']
    for value in newDic:
        tmpDic=value
        podData=tmpDic['metadata']
        if podData['name'] not in fullDic.keys():
            tmpvalues=podData['name']
            fullDic[tmpvalues]=[]
    os.remove('all-pods.json')
    for value in fullDic.keys():
        result=os.popen('curl -X GET '+masterUrl+'/api/v1/namespaces/default/pods/'+value+' --header "Authorization: Bearer '+TOKEN+'" --insecure | jq .status.phase').read()
        fullDic[value].append(result)

    Output=open('latest.txt','w')
    for result in fullDic.keys():
        List=fullDic[result]
        tmp=List[0]
        Output.write(result + ' : '+tmp+'                                                                                   \n')
    Output.close()
    latest=open('latest.txt','r')
    os.remove('latest.txt')
    out=latest.read()
    return out