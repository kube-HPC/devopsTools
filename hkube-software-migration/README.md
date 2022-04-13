# hkube-software-migration
this tool use to migration pipelines between hkube softwares
requierments:
    -   linux machine
    -   jq , zip (should allready exists on the machine)
# 
    - verify that you are connect to your docker registry
    - running from linux machine
    - if you store pipeline before you create his algos it will failed 
    - hkubectl binaries are rquire for the script. (as part of the repo)

# how to use?

# step 1
    - edit the inputJsonFile.json with the rquired pipelines you want to collect from your hkube cluster
# step 2
    -  run ./main.sh {endpoint_url}
       example: ./main.sh 'hkubelocal/hkube/dashboard/#/'
# step 3
    outputs: 
    data/
    └── pipelines
        ├── fibonacci-pipeline
        │   ├── algos
        │   │   ├── errors.txt
        │   │   ├── fibonacci-algorithm.tar.gz
        │   │   ├── fibonacci-algorithm.yaml
        │   │   ├── images.txt
        │   │   └── output.json
        │   └── fibonacci-pipeline.json
        └── stringReplace
            ├── algos
            │   ├── errors.txt
            │   ├── eval-alg.tar.gz
            │   ├── images.txt
            │   └── output.json
            └── stringReplace.json

# step 4
    publish algorithm to new enviorment:
    command: hkubectl --endpoint={endpoint_url} algorithm apply ./data/pipelines/fibonacci-pipeline/algos/fibonacci-algorithm.yaml

    publish pipeline to new enviorment:
    command: hkubectl --endpoint={endpoint_url} pipeline store ./data/pipelines/fibonacci-pipeline/fibonacci-pipeline.json