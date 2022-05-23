import os
import subprocess
import json
from flask import jsonify
from flask import Flask
import flask

app = Flask(__name__)
TOKEN=os.popen('cat /var/run/secrets/kubernetes.io/serviceaccount/token').read()
masterUrl= os.getenv('MASTER_CLUSTER_IP')
etcdReplicas= os.getenv('ETCD_REPLICAS')
redisReplicas= os.getenv('REDIS_REPLICAS')
redisPrefix='hkube-redis-ha-server'
etcdPrefix='hkube-etcd'
giteaPrefix='hkube-gitea'
mongoPrefix='hkube-mongodb'

@app.route("/health")
def health():
    errorDic={}
    coreFailed=0
    thirdPFailed=0
    fullDic={}
    redisResult={}
    etcdResult={}
    giteaResult={}
    mongoResult={}
    coreResult={}
    os.system('rm -rf result.txt')
    os.system('curl -X GET '+str(masterUrl)+'/api/v1/namespaces/default/pods/ --header "Authorization: Bearer '+str(TOKEN)+'" --insecure | jq .items > all-pods.json')
    with open('all-pods.json', 'r') as jsonfile:
        allPods = json.load(jsonfile)
    os.remove('all-pods.json')
    
    for value in allPods:
        tmpDic=value
        podData=tmpDic['metadata']['name']
        if podData not in fullDic.keys():
            fullDic[podData]=tmpDic['status']      
    # check_redis,etcd
    for pod in fullDic.keys():
        flag=1
        if redisPrefix in pod:
            flag=0
            redisResult[str(redisPrefix)+'-'+str(len(redisResult.keys()))]=[]
        if etcdPrefix in pod:
            flag=0
            etcdResult[str(etcdPrefix)+'-'+str(len(etcdResult.keys()))]=[]
        if  giteaPrefix in pod:
            flag=0
            giteaResult[str(giteaPrefix)+'-'+str(len(giteaResult.keys()))]=[]
        if  mongoPrefix in pod:
            flag=0
            mongoResult[str(mongoPrefix)+'-'+str(len(mongoResult.keys()))]=[]
        if flag == 1:
            coreResult[str(pod)]=[] 

    for value in fullDic.keys():
        temp=fullDic[value]
        containerList=temp['containerStatuses']
        for value2 in containerList:
            status=str(value2['state'].keys()).replace("dict_keys(['","").replace("'])","")
            if status != 'running':
                if value in coreResult.keys():
                    coreFailed=1
                    errorDic[value]=containerList
                else:
                    thirdPFailed=1
                    errorDic[value]=containerList

    
    returnFile=open('result.txt','w')
    returnFile.write('Hkube Health Check\n------------------\n\nSUMMARY\n--------\n')
    returnFile.write('\n  CORE\n  --------\n')
    if coreFailed == 1:
        returnFile.write('  cluster core not healthy ! please check logs\n')    
    if coreFailed == 0:
         returnFile.write('  all cluster pods core healthy !\n')
    returnFile.write('\n  THIRD_PARTY\n  --------\n')
    if thirdPFailed == 1:
        returnFile.write('  cluster thirdparty pods not healthy ! please check logs\n')    
    if thirdPFailed == 0:
        returnFile.write('  all cluster pods thirdparty healthy !\n')    
    if int(len(etcdResult)) != int(etcdReplicas):
        returnFile.write('\n  there are issue with the replicas of etcd.\n    replicas: '+str(etcdReplicas)+'\n    exists: '+str(len(etcdResult)))
    if int(len(redisResult)) != int(redisReplicas):
        returnFile.write('\n\n  there are issue with the replicas of redis.\n    replicas: '+str(redisReplicas)+'\n    exists: '+str(len(redisResult)))
    if coreFailed == 0 and thirdPFailed == 0:
        returnFile.write('\n\n\n\nNO ERROR LOGS NEEDED\n')
    else:
        returnFile.write('\n\n\n\nFULL ERROR LOGS\n-----------------\n')
        #returnFile.write(str(errorDic))
        for errorPod in errorDic.keys():
            returnFile.write('\n\n  Pod Name: '+errorPod+'\n--------------------\n')
            for container in errorDic[errorPod]:
                returnFile.write('\n    Container Name: '+str(container['name']))
                returnFile.write('\n    Container Status: '+str(container['state'].keys()).replace("dict_keys(['","").replace("'])","")+'')
                massage=container['state']
                try:
                    temp=massage['waiting']
                    reason=temp['reason']
                    massage=temp['message']
                    returnFile.write('\n    Reason: '+reason  )
                    returnFile.write('\n    message: '+massage  +'\n')
                except:
                    temp=massage['running']
                    started=temp['startedAt']
                    returnFile.write('\n    Start at: '+started +'\n')
    returnFile.close()
    
    
    
    return flask.send_file("result.txt")
