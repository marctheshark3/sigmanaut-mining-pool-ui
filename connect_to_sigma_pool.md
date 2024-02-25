# How to Connect to the Sigmanaut Mining Pool

Currently there are two ports one for high hashrate and another for low hashrate. 

POOL URL:
74.69.128.24

High Hash Port: 3053
Low Hash Port: 3052

## HIVEOS
1. Create New Flight Sheet
2. Pool set to configure in miner
3. Set "POOL URL" to 74.69.128.24:<port>
  1. For High HASH: 74.69.128.24:3053
  2. For Low HASH: 74.69.128.24:3052

## MMPOS
1. Create a new pool in Management
2. In Hostname enter the URL: 74.69.128.24
3. Enter the Pools Port either low or high hash port: 3053

## Linux OR Windows
1. edit the .sh file for the specific miner
2. in the pool argument enter the full url with port of choice
  1. ```
      POOL=74.69.128.24:3053
      WALLET=9ehJZvPDgvCNNd2zTQHxnSpcCAtb1kHbEN1VAgeoRD5DPVApYkk.Capitol_Peak
      ./lolMiner --algo AUTOLYKOS2 --pool $POOL --user $WALLET $@
      while [ $? -eq 42 ]; do
      sleep 10s
      ./lolMiner --algo AUTOLYKOS2 --pool $POOL --user $WALLET $@
      done
      ```
