#!/bin/bash

#create workspace
rm -rf data
mkdir -p data/pipelines/
PIEPLINES_LIST=$(echo inputJsonFile.json)
END=$1
#'https://playground.hkube.io/#/'

#loop on pipelines
jq -c '.[]' $PIEPLINES_LIST | while read i; do
    echo "collect data from $i"
    i="${i#?}" && i="${i%?}"
    mkdir -p data/pipelines/$i
    ./hkubectl --endpoint=$END pipeline get $i -j | jq .result > ./data/pipelines/$i/$i.json
    GetAlgos=$(./hkubectl --endpoint=$END pipeline get $i -j | jq .result.nodes)
    mkdir -p data/pipelines/$i/algos/
    echo $GetAlgos | jq . > data/pipelines/$i/algos/output.json
    touch data/pipelines/$i/algos/images.txt
    touch data/pipelines/$i/algos/errors.txt
    list=$(jq '.[] .algorithmName' data/pipelines/$i/algos/output.json )
    for value in $list
    do
        value="${value#?}" && value="${value%?}"
        echo $value
        imageToPull=$(./hkubectl --endpoint=$END algorithm get $value -j | jq .algorithmImage)
        imageBuildVersion=$(./hkubectl --endpoint=$END algorithm get $value -j | jq .version)
        gpuUse=$(./hkubectl --endpoint=$END algorithm get $value -j | jq .gpu)
        memory=$(./hkubectl --endpoint=$END algorithm get $value -j | jq .mem)
        cpu=$(./hkubectl --endpoint=$END algorithm get $value -j | jq .cpu)
        reservedmemory=$(./hkubectl --endpoint=$END algorithm get $value -j | jq .reservedMemory)
        minhotworkers=$(./hkubectl --endpoint=$END algorithm get $value -j | jq .minHotWorkers)
        type=$(./hkubectl --endpoint=$END algorithm get $value -j | jq .type)
        imageToPull="${imageToPull#?}" && imageToPull="${imageToPull%?}"
        grep $imageToPull data/pipelines/$i/algos/images.txt
        if [ $? == 0 ]
        then
            echo 'look like image allready pull , continue to the next require image'
        else
            echo $value : $imageToPull >> data/pipelines/$i/algos/images.txt
            echo "start download image $imageToPull"
            if ! docker pull $imageToPull; then
                echo "there are issue to pull $imageToPull" >> data/pipelines/$i/algos/errors.txt
            else
                docker save $imageToPull | gzip > data/pipelines/$i/algos/$value.tar.gz 
            fi
        fi
        {
        echo name: $value
        echo cpu: $cpu
        echo gpu: $gpuUse
        echo mem: $memory
        echo reservedMemory: $reservedmemory 
        echo minHotWorkers: $minhotworkers
        echo algorithmImage: $imageToPull
        echo type: Image
        } >> data/pipelines/$i/algos/$value.yaml


    done
    done
    zip -r data$( date +"%S-%M-%H_%m-%d-%y").zip ./data/
    rm -rf data/