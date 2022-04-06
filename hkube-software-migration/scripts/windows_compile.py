import os
import json
import sys
import shutil
import subprocess

currentDir=os.getcwd()
hkubeUrl=sys.argv[1]

if os.path.isdir(currentDir+'/data'):
    shutil.rmtree(currentDir+'/data/')


os.mkdir(currentDir+'/data/')
os.mkdir(currentDir+'/data/pipelines')
jsonFile=open('inputJsonFile.json')
pipelineList=json.load(jsonFile)

for value in pipelineList:
    os.mkdir(currentDir+'/data/pipelines/'+value)
    print('collect data from '+value)
    output=os.system('bin/hkubectl --endpoint='+hkubeUrl+' pipeline get '+value+' -j > data/pipelines/'+value+'/'+value+'.json')
    jsonParser=open(currentDir+'/data/pipelines/'+value+'/'+value+'.json')
    tempJson=json.load(jsonParser)
    print(tempJson['result'])