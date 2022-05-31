import os
import subprocess
import json
from flask import jsonify
from flask import Flask
import flask
from storage import HKUBE_CORE,HKUBE_THIRD_PARTY


app = Flask(__name__)
TOKEN=os.popen('cat /var/run/secrets/kubernetes.io/serviceaccount/token').read()
masterUrl= os.getenv('MASTER_CLUSTER_IP')
allPods={}
@app.route("/health")
def health():
    def createDic(dic,label,error,types):
        # Create Dictionary 
        tempDic={}
        tempDic['pod_name']=dictionaryMain['metadata']['name']
        tempDic['node_name']=dictionaryMain['spec']['nodeName']
        tempDic['service_account_name']=dictionaryMain['spec']['serviceAccount']
        tempDic['containers_count']=str(len(dictionaryMain['spec']['containers']))
        tempDic['containers_details']=[]
        containerDic={}
        try:
            for value in dictionaryMain['status']['containerStatuses']:
                containerDic['name']=value['name']
                containerDic['image_name']=value['image']
                containerDic['status']=value['state']
                tempDic['containers_details'].append(containerDic)
            dic[label]=tempDic
            for failed in dictionaryMain['status']['containerStatuses']:
                if failed['ready'] == False:
                    tempDic['type']=types
                    errorD[dictionaryMain['metadata']['name']]=tempDic
        except:
            errorD[dictionaryMain['metadata']['name']]=tempDic
    def printOut(dictionaryToPrint,writeto):
        for value in dictionaryToPrint:
            writeto.write('\n---\n')
            # writeto.write('type: hkube-cores')
            writeto.write('deployment: '+value+'\n')
            a=dictionaryToPrint[value]
            for value2 in a.keys():
                if type(a[value2]) == str:
                    writeto.write('    '+value2 + ': '+str(a[value2])+'\n')
                elif type(a[value2]) == list:
                    temp=a[value2]
                    for value in temp:
                        Dic=value
                        for var in Dic.keys():
                            writeto.write('        '+var +' : '+str(Dic[var])+'\n')

    def init():
        os.system('rm -rf result.txt')
        os.system('curl -X GET '+str(masterUrl)+'/api/v1/namespaces/default/pods/ --header "Authorization: Bearer '+str(TOKEN)+'" --insecure | jq .items > all-pods.json')

        with open('all-pods.json', 'r') as jsonfile:
            all = json.load(jsonfile)
        return all
    allPods={}
    allPods=init()
    os.remove('all-pods.json')
    errorD={}
    coresD={}
    thirdPartyD={}
    unknownD={}


    for dictionaryMain in allPods:
        try:
            labelName=dictionaryMain['metadata']['labels']['app']
            if labelName in HKUBE_THIRD_PARTY:
                thirdPartyD[labelName]={}
                createDic(thirdPartyD,labelName,'third-party')
            elif labelName in HKUBE_CORE:
                coresD[labelName]={}
                createDic(coresD,labelName,errorD,'hkube-cores')
            else:
                unknownD[labelName]={}
                createDic(unknownD,labelName,errorD,'third-party')
        except:
                unknownD[labelName]={}
                createDic(unknownD,labelName,errorD,'third-party')
    

    result=open('result.txt','w')
    result.write('-----------------\nHKUBE HEALTH CHECK\n-----------------\n')
    if len(errorD):
        result.write('\nPod Error list:\n-----------------\n')
        for value in errorD.keys():
            result.write('error in pod: '+value+'\n')
        result.write('\nsee error logs below')
        printOut(errorD,result)
    else:
        result.write('\nno errors!\n-----------------\n')
    result.write('\nHKUBE CORE FULL LOGS:\n-----------------\n')
    printOut(coresD,result)
    result.write('THIRD PARTY FULL LOGS:\n-----------------\n')
    printOut(thirdPartyD,result)
    printOut(unknownD,result)

    result.close()
    return flask.send_file("result.txt")
