# how to use 

# build image with the dockerfile .

- docker build . -t {imageNameYouWant}
- save the image in private/public registry . 
- connect to your cluster and run: kubectl apply -Rf ./yamls
- edit the env section in deployments to your master-cluster-ip
# purpose 
- use for check if the pods are running , include all pods , http://hkubelocal/health
