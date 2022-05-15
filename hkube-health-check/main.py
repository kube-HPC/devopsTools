import os
import subprocess
import json
from flask import jsonify
from flask import Flask
import flask

app = Flask(__name__)
#TOKEN=os.popen('cat /var/run/secrets/kubernetes.io/serviceaccount/token').read()
TOKEN='eyJhbGciOiJSUzI1NiIsImtpZCI6IjUzbUNhQWNvQm4zYU9ER3RZemhhak5uU0FNVnNlYzZmal81bnhlR1NNUDgifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJkZWZhdWx0Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZWNyZXQubmFtZSI6ImFsZ29yaXRobS1vcGVyYXRvci1zZXJ2aWNlYWNjb3VudC10b2tlbi14OWM5dyIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50Lm5hbWUiOiJhbGdvcml0aG0tb3BlcmF0b3Itc2VydmljZWFjY291bnQiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC51aWQiOiIxNjU2YTlmOC1jOThiLTQwZmEtOGVmZi01ZDdiYTcwM2UyMTEiLCJzdWIiOiJzeXN0ZW06c2VydmljZWFjY291bnQ6ZGVmYXVsdDphbGdvcml0aG0tb3BlcmF0b3Itc2VydmljZWFjY291bnQifQ.RfuFrl906-ZW75pSYzMjJ2RTq5mnvK9FyqnoUgarg0TxfFwXCH8VToMIIuPiXF5JUp0H75Du5cnAAnyk_lbFXX1518ZPZ_BZ-6axCLE7tNAKkNaRu8HIlscMfjDNUkY2McAmJDKn2rLypqrV2FVwXJ0vgGD8QbMd9KwVY61AwNIHMFxjPeutLTu1fwiZAxilKlE0T5EYBgpAnraaZEc_uVdMzQw-mC_YvAV07URaxqnWoaqzV965oB1qJioK4zroBUvlqY5iMqssJzFEJ1J5bwzmXSNHREI2HwLWKrfLFaWyD9Dtw_-aFj3q83e6egGmv_yA2UIANCLYcj_bHNodjg'
masterUrl='https://192.168.49.2:8443'
etcdReplicas='3'
redisReplicas='3'
#masterUrl= os.getenv('MASTER_CLUSTER_IP')
#etcdReplicas= os.getenv('ETCD_REPLICAS')
#redisReplicas= os.getenv('REDIS_REPLICAS')
redisPrefix='hkube-redis-ha-server'
etcdPrefix='hkube-etcd'
currentStatus='.status.containerStatuses'

@app.route("/health")
def health():

    fullDic={}
    redisResult={}
    etcdResult={}
    os.system('rm -rf result.txt')
    returnFile=open('result.txt','w')
    returnFile.write('Hkube Health Check\n------------------\n\n')
    os.system('curl -X GET '+str(masterUrl)+'/api/v1/namespaces/default/pods/ --header "Authorization: Bearer '+str(TOKEN)+'" --insecure | jq . > all-pods.json')
    with open('all-pods.json', 'r') as jsonfile:
        allPods = json.load(jsonfile)
    newDic=allPods['items']
    os.remove('all-pods.json')
    for value in newDic:
        tmpDic=value
        podData=tmpDic['metadata']
        if podData['name'] not in fullDic.keys():
            tmpvalues=podData['name']
            fullDic[tmpvalues]=[]
    #check_redis,etcd
    for pod in fullDic.keys():
        if redisPrefix in pod:
            redisResult[str(redisPrefix)+'-'+str(len(redisResult.keys()))]=[]
        if etcdPrefix in pod:
            etcdResult[str(etcdPrefix)+'-'+str(len(etcdResult.keys()))]=[]


    # collect data: status  
    for value in redisResult.keys():
        podDic={}
        os.system('curl -X GET '+str(masterUrl)+'/api/v1/namespaces/default/pods/'+value+' --header "Authorization: Bearer '+str(TOKEN)+'" --insecure | jq '+currentStatus+' > '+value+'.json')
        with open(value+'.json','r') as valueJsonFile:
            jsonValue= json.load(valueJsonFile)
        redisResult[value]=jsonValue
    for value2 in etcdResult.keys():    
        os.system('curl -X GET '+str(masterUrl)+'/api/v1/namespaces/default/pods/'+value2+' --header "Authorization: Bearer '+str(TOKEN)+'" --insecure | jq '+currentStatus+' > '+value2+'.json')
        with open(value2+'.json','r') as valueJsonFile:
            jsonValue= json.load(valueJsonFile)
        etcdResult[value2]=jsonValue
    os.system('rm -rf hkube-etcd*.json && rm -rf hkube-redis*.json')
    
    returnFile.write('Redis\n---------\n')
    if int(redisReplicas) > len(redisResult.keys()):
        returnFile.write('\n  replicas:' + redisReplicas)
        returnFile.write('\n  replicas and exists pods are not match, please check!')
    else:
        returnFile.write('\n  replicas:' + redisReplicas)
        returnFile.write('\n  replicas and exists pods are match!')
    for value in redisResult.keys():
        returnFile.write('\n\n  '+value+'\n  ------------')
        temp=redisResult[value]
        for container in temp:
            returnFile.write('\n    Name: '+container['name']+'')
            returnFile.write('\n    state: \n')
            temp1=container['state']
            for value in temp1.keys():
                returnFile.write('      '+str(value)+' :'+str(temp1[value])+'\n')
            returnFile.write('      Ready: '+str(container['ready']))



    returnFile.write('\n\n\nEtcd\n---------\n')
    if int(etcdReplicas) > len(etcdResult.keys()):
        returnFile.write('\n    replicas:' + etcdReplicas)
        returnFile.write('\n    replicas and exists pods are not match, please check!')
    else:
        returnFile.write('\n    replicas:' + etcdReplicas)
        returnFile.write('\n    replicas and exists pods are match!')
    for value in etcdResult.keys():
        temp=etcdResult[value]
        for container in temp:
            returnFile.write('\n\n  '+value+'\n  ------------')
            returnFile.write('\n    Name: '+container['name']+'\n')
            returnFile.write('\n    state: \n')
            temp1=container['state']
            for value in temp1.keys():
                returnFile.write('      '+str(value)+' :'+str(temp1[value])+'\n')
            returnFile.write('      Ready: '+str(container['ready'])+'\n')

    returnFile.close()
    return flask.send_file("result.txt")