import os
import subprocess
import json
from flask import jsonify
from flask import Flask
import flask
def init(masterUrl,TOKEN,api,types):
    if types == 'metrics-server':
        os.system('curl -X GET '+str(masterUrl)+api+' --header "Authorization: Bearer '+str(TOKEN)+'" --insecure | jq . > all-'+types+'.json')    
    else:
        os.system('curl -X GET '+str(masterUrl)+api+' --header "Authorization: Bearer '+str(TOKEN)+'" --insecure | jq .items > all-'+types+'.json')
    with open('all-'+types+'.json', 'r') as jsonfile:
        all = json.load(jsonfile)
    os.remove('all-'+types+'.json')
    return all

def validateAccess(checkListApiVerison):
    result=open('health-main.html','w')
    result.write('''
    <!DOCTYPE html>
    <html>
    <body>
    <h1>Hkube Health Check:</h1>

    <p><a href="/health/pods">pods</a> - output error defails about pods</p>
    <p><a href="/health/deployments">deployments</a> - output error defails about deployments</p>
    <p><a href="/health/statefulsets">statefulsets</a> - output error defails about statefulsets</p>
    <p><a href="/health/nodes">nodes</a> - output defails about nodes</p>
    <p><a href="/health/storageclasses">storageclasses</a> - output storageClass details</p>
    <p><a href="/health/persistentvolumeclaims">persistentvolumeclaims</a> - output persistentvolumeclaims details</p>
    <p><a href="/health/metrics">metrics</a> - print this output</p>
    <p><a href="/health">health</a> - print this output</p>
    
    
    <h1>Route List Permissions Validate:</h1>
    ''')

    for key , value in checkListApiVerison.items():
        os.system('curl -X GET '+str(masterUrl)+value+' --header "Authorization: Bearer '+str(TOKEN)+'" --insecure | jq . > '+key+'.json')
        with open(key+'.json','r') as jsonfile:
            dictionary=json.load(jsonfile)
        os.system('rm -f '+key+'.json')
        try:
            if 'reason' in dictionary.keys():
                result.write('<p> '+key+':    no access, Failed to get data about '+key+'</p>')
            else:
                result.write('<p> '+key+':    access verified</p>')
        except:
            result.write('<p> '+key+':    no access, Failed to get data about '+key+'</p>')
    result.write('''
    </body>
    </html>
    ''')
    result.close()

def podAnalyze(tempDic):
    finalDic={}
    for pod in tempDic:
        if pod["metadata"]["name"] not in finalDic.keys():
            tempPodDic={}
            tempPodDic['container-count']=len(pod['spec']['containers'])
            try:
                tempPodDic['container-status']=pod['status']['containerStatuses']
                for value in pod['status']['containerStatuses']:
                    for key ,var in value['state'].items():                    
                        if key != 'running':
                            tempPodDic['state'] = 'failed'
                finalDic[str(pod["metadata"]["name"])]=tempPodDic
            except:
                tempPodDic['container-status']=['unknown']
                tempPodDic['state'] = 'failed'
                finalDic[str(pod["metadata"]["name"])]=tempPodDic
    return finalDic

def deploymentAnalyze(tempDic):
    temp={}
    for value in tempDic:
        d={}
        d['replicas']=value['status']['replicas']
        if 'unavailableReplicas' in value['status'].keys():
           d['status'] = 'failed'
           d['unavailableReplicas']=value['status']['unavailableReplicas']
           d['replicas']=value['status']['replicas']
        else:
            d['status'] = 'success'
            d['replicas']=value['status']['replicas']

        temp[value['metadata']['name']]=d
    return temp

def collectLogs(error):
    for value in error:
        error[value]['logs']=os.popen('curl -X GET '+str(masterUrl)+'/api/v1/namespaces/default/pods/'+value+'/log --header "Authorization: Bearer '+str(TOKEN)+'" --insecure | tail -n 20').read()

def checkStatus(value,d,resultFile):
    resultFile.write('<h4>&emsp;Container Logs</h4>')
    noLogs=1
    try:
        tmp = json.loads(value)
        resultFile.write('<p>&emsp;Status: '+tmp['status']+'</p>')
        resultFile.write('<p>&emsp;message: '+tmp['message']+'</p>')

    except:
        if noLogs==1:
            resultFile.write('<p>&emsp;'+value+'</p>')

def checkService(lists):
    if lists == None:
        return False
    if type(lists) == dict:
        if 'reason' in lists.keys():
            return False
    return True
# Main Values
app = Flask(__name__)
TOKEN=os.popen('cat /var/run/secrets/kubernetes.io/serviceaccount/token').read()
masterUrl= os.getenv('MASTER_CLUSTER_IP')
allPods={}
checkListApiVerison={'pods':'/api/v1/namespaces/default/pods',
                    'deployments':'/apis/apps/v1/namespaces/default/deployments',
                    'statefulsets':'/apis/apps/v1/namespaces/default/statefulsets',
                    'nodes':'/api/v1/nodes',
                    'storageclasses':'/apis/storage.k8s.io/v1/storageclasses',
                    'persistentvolumeclaims':'/api/v1/namespaces/default/persistentvolumeclaims',
                    'metrics-server':'/apis/metrics.k8s.io/v1beta1/'}
###############

#Help Output
@app.route("/health")
def main():
    if os.path.isfile('./health-main.html'):
        os.remove('./health-main.html')
    validateAccess(checkListApiVerison)
    return flask.send_file("health-main.html")

#Pod Data Output
@app.route("/health/pods")
def pods():
    podlist=init(masterUrl,TOKEN,checkListApiVerison['pods'],'pod')
    answer=checkService(podlist)
    result=open('result.html','w')
    if answer == True:
        temp=podAnalyze(podlist)        
        errorDic={}
        for value in temp:
            if 'state' in temp[value].keys():
                errorDic[value]=temp[value]
        collectLogs(errorDic)
        result.write('<h1>Hkube Pods Health</h1>')
        if len(errorDic.keys()):
            result.write('<h2>error found in pods:</h2>')
            for var in errorDic.keys():
                result.write('<p>'+var+'</p>')
            result.write('<p>-------------------------</p>')
            for value in errorDic:
                result.write('<h4>Pod Name: '+value+'</h4>')
                try:
                    result.write('<p>Replicas: '+str(errorDic[value]['replicas'])+'</p>')
                except:
                    result.write('<p>Replicas: Unknown</p>')
                result.write('<p>Container Count: '+str(errorDic[value]['container-count'])+'</p>')
                result.write('<p>Containers Status:</p>')
                for value1 in errorDic[value]['container-status']:
                    try:
                        result.write('<p>&emsp;container Name: '+str(value1['name'])+'</p>')
                        result.write('<p>&emsp;container state: '+str(value1['state'].keys()).replace("dict_keys(['","").replace("'])","")+'</p>')
                        for key,va in value1['state'][str(value1['state'].keys()).replace("dict_keys(['","").replace("'])","")].items():
                            result.write('<p>&emsp;&emsp;'+key+': '+va+'</p>')
                    except:
                        result.write('<p>&emsp;&emsp;failed to get data from '+value+'</p>')
                checkStatus(errorDic[value]['logs'],value,result)
        else:
            result.write('''
            <!DOCTYPE html>
            <html>
            <body>
            <h2> all pods active </h2>
            ''')
            for var in temp:
                result.write('<p>'+var+'&emsp;<a href="/health/pods/logs/'+var+'">Logs</a></p>')
            result.write('''
            </html>
            </body>
            ''')
        result.close()
    else:
        result.write('No Access\nPlease Verify service account role')
        result.close()
    return flask.send_file("result.html")

#Deployments Data Output
@app.route("/health/deployments")
def deployments():
    if os.path.isfile('./health-deployments.html'):
        os.remove('./health-deployments.html')
    result=open('health-deployments.html','w')
    deployments=init(masterUrl,TOKEN,checkListApiVerison['deployments'],'deployments')
    answer=checkService(deployments)
    if answer == True:
        temp=deploymentAnalyze(deployments)
        error=0
        errorDicDep={}
        for value in temp:
            if 'unavailableReplicas' in temp[value].keys():
                errorDicDep[value]=temp[value]
        
        if len(errorDicDep):
            result.write('<h1>Hkube Deployments Health</h1>')
            result.write('<h2>Error found in deployments</h2>')
            for k,v in errorDicDep.items():
                result.write('<p>'+str(k) + ': '+str(v)+'</p>')
            result.close()
        else:
            result.write('<h1>Hkube Deployments Health</h1>')
            result.write('<h2>all deployments active</h2>')
            for v in deployments:
                result.write('<p>'+v['metadata']['name']+' - Running</p>')
            result.close()
        return flask.send_file("health-deployments.html")
    else:
        result.write('<p>No Access , Please Verify service account role</p>')
        result.close()
        return flask.send_file('health-deployments.html')

#Statefulsets Data Output
@app.route("/health/statefulsets")
def statefulset():
    error=0
    if os.path.isfile('./health-statefulsets.html'):
        os.remove('./health-statefulsets.html')
    result=open('health-statefulsets.html','w')
    temp=init(masterUrl,TOKEN,checkListApiVerison['statefulsets'],'statefulsets')
    answer=checkService(temp)
    if answer == True:
        result.write('<h1>Hkube Statefulsets Health</h1>')
        for stateful in temp:
            try:
                if int(stateful['status']['readyReplicas']) < int(stateful['status']['replicas']):
                    error=1
                    result.write('<p>Found error in '+stateful['metadata']['name']+'</p><p>Replicas: '+str(stateful['status']['replicas'])+'</p>Ready Replcas: '+str(stateful['status']['readyReplicas']))
            except:
                print()
        if error == 0:
            result.write('<p>all Statefulsets are active</p>')
            for v in temp:
                result.write('<p>'+v['metadata']['name']+' - Running</p>')
            result.close()
        result.close()
        return flask.send_file("health-statefulsets.html")
    else:
        result.write('<p>No Access , nPlease Verify service account role</p>')
        result.close()
    return flask.send_file("health-statefulsets.html")
#Node Data Output
@app.route("/health/nodes")
def nodes():
    result=open('nodes.txt','w')
    result.write('Cluster Nodes\n-----------------\n\n')
    nodeList=init(masterUrl,TOKEN,checkListApiVerison['nodes'],'nodes')
    if nodeList:
        for v in nodeList:
            result.write('\n    name: '+v['metadata']['name']+'\n')
            result.write('    operate system: '+v['status']['nodeInfo']['osImage']+'\n')
            print(v['status']['allocatable']['memory'])
            result.write('    resources:\n      cpu: '+v['status']['allocatable']['cpu']+'\n      memory: '+str(int(v['status']['allocatable']['memory'].replace('Ki','')) / 1024)+'MB\n')
            for va in v['status']['conditions']:
                if va['type'] == 'Ready' and va['status'] == 'True':
                    result.write('    ready: True\n')
                if va['type'] == 'Ready' and va['status'] == 'False':
                    result.write('    ready: False\n')
    else:
        return('    no access!\nplease verify service account role.\n')


    result.close()
    return flask.send_file("nodes.txt")

# StorageClass Data Output
@app.route("/health/storageclasses")
def storageclasses():
    storagelist=init(masterUrl,TOKEN,checkListApiVerison['storageclasses'],'storageclasses')
    answer=checkService(storagelist)
    result=open('storageclasses.txt','w')
    if answer == True:
        result.write('storageClasses\n----------------\n')
        for value in storagelist:
            result.write('\nName: '+value['metadata']['name'])
            result.write('\nProvisioner: '+value['provisioner'])
            result.write('\nStorageClass is Default: '+value['metadata']['annotations']['storageclass.kubernetes.io/is-default-class'])
            result.close()
        return flask.send_file('storageclasses.txt')
    else:
        result.write('No Access\nPlease Verify service account role')
        result.close()
    return flask.send_file("storageclasses.txt")        
# persistentvolumeclaims Data Output
@app.route("/health/persistentvolumeclaims")
def persistentvolumeclaims():
    persistent=init(masterUrl,TOKEN,checkListApiVerison['persistentvolumeclaims'],'persistentvolumeclaims')
    resultpvc=open('persistentvolumeclaims.txt','w')
    answer=checkService(persistent)
    if answer == True:
        resultpvc.write('PersistentVolumeClaims\n-----------------------\n')
        for v in persistent:
            resultpvc.write('\nname: ' +v['metadata']['name']+'\n')
            resultpvc.write('    phase: '+v['status']['phase']+'\n')
            resultpvc.write('    '+str(v['status']['capacity']).replace('{','').replace('}','')+'\n')
            resultpvc.write('-------------------------------------\n')
        resultpvc.close()
        return flask.send_file('persistentvolumeclaims.txt')
    else:
        resultpvc.write('No Access\nPlease Verify service account role')
        resultpvc.close()
    return flask.send_file("persistentvolumeclaims.txt")

@app.route('/health/pods/logs/<pod>')
def logs(pod):
   logs=os.popen('curl -X GET '+str(masterUrl)+'/api/v1/namespaces/default/pods/'+pod+'/log --header "Authorization: Bearer '+str(TOKEN)+'" --insecure ' ).read()
   return logs

@app.route("/health/metrics")
def metrics():
    # masterUrl,TOKEN,api,types
    metricList=init(masterUrl,TOKEN,checkListApiVerison['metrics-server'],'metrics-server')
    answer=checkService(metricList)
    result=open('metrics.html','w')
    if answer == True:
        result.write('<h1>Hkube Metrics</h1>')
        # print(metricList)
        for value in metricList['resources']:
            result.write('&emsp;<a href="/health/metrics/'+value['name']+'">'+value['name']+'</a></p>')
        result.close()
        return flask.send_file("metrics.html")
    else:
        result.write('No Metrics server exists/there is no access to service')
        result.close()
        return flask.send_file("metrics.html")

@app.route("/health/metrics/nodes")
def nodesMetrics():
    os.system('curl -X GET '+str(masterUrl)+checkListApiVerison['metrics-server']+'nodes --header "Authorization: Bearer '+str(TOKEN)+'" --insecure  | jq . > node-metrics.json')
    with open('node-metrics.json' ,'r') as jsonfile:
        all = json.load(jsonfile)    
    result=open('result.html','w')
    result.write('<h1>Nodes Resoucres</h1>')
    for value in all['items']:
        result.write('<h3>'+value['metadata']['name']+'</h3>')
        tmp=value['usage']
        result.write('<p>cpu: '+str(int(str(tmp['cpu']).replace('n',''))/1000000)+'-m</p>')
        result.write('<p>memory: '+str(int(str(tmp['memory']).replace('Ki',''))/1024)+'-MB</p>')

    result.close()
    return flask.send_file('result.html')

@app.route("/health/metrics/pods")
def podsMetrics():
    os.system('curl -X GET '+str(masterUrl)+checkListApiVerison['metrics-server']+'pods --header "Authorization: Bearer '+str(TOKEN)+'" --insecure  | jq . > node-metrics.json')
    result=open('result.html','w')
    result.write('<h1>Pods Resoucres</h1>')
    with open('node-metrics.json' ,'r') as jsonfile:
        all = json.load(jsonfile)
    for  value in all['items']:
        for v in value['containers']:
            result.write('<h3>'+v['name']+'</h3>')
            tmp=v['usage']
            result.write('<p>cpu: '+str(int(str(tmp['cpu']).replace('n',''))/1000000)+'-m</p>')
            result.write('<p>memory: '+str(int(str(tmp['memory']).replace('Ki',''))/1024)+'-MB</p>')
    result.close()
    return flask.send_file("result.html")

