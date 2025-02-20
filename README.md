# Sigmanauts Mining Pool

## Telegram Group
[Join our Telegram group!](https://t.me/sig_mining)


## UI Configuration
Enter you Wallet Address in the input tab when you start up the dashboard

## UI Operation
```
# USING LATEST DOCKER IMAGE FROM GIT
docker compose down # Stops the UI
docker compose pull # pulls the latest docker image
docker compose up -d # Runs the UI


# ALTERNATIVELY YOU CAN BUILD IT YOURSELF
git pull # ensure you have latest files from git
docker compose up --build
```

In a web browser you can navigate to: http://localhost:8050/

## How to Connect to the Sigmanaut Mining Pool

### Choose a PORT

Based on your hashrate and TLS specificity choose the port that is right for you. 

- Port 3052 - Lower than 10GH/s - No TLS
- Port 3053 - Higher than 10GH/s - No TLS
- Port 3054 - Lower than 10GH/s - TLS
- Port 3055 - Higher than 10GH/s - TLS

POOL URL:
15.204.211.130

### HIVEOS - Assuming Port 3052
1. Create a New Flight Sheet
2. Pool set to configure in miner
3. Set "POOL URL" to 15.204.211.130:3052


### MMPOS - Assuming Port 3052
1. Create a new pool in Management
2. In Hostname enter the URL: 15.204.211.130
3. Port: 3052

### Linux OR Windows - Assuming Port 3052
1. edit the .sh file for the specific miner, in this case lolminer
2. in the pool argument enter the full url with port of choice
```
POOL=15.204.211.130:3052
WALLET=your_wallet_address
./lolMiner --algo AUTOLYKOS2 --pool $POOL --user $WALLET $@
while [ $? -eq 42 ]; do
sleep 10s
./lolMiner --algo AUTOLYKOS2 --pool $POOL --user $WALLET $@
done
```

### Tip
If you find this tool helpful and wish to support its development, feel free to leave a tip! Your support is greatly appreciated and helps ensure continued improvements and updates. Thank you for considering! 

ERGO ADDRESS: 9f2nrcC2NHsx96RmN52g3GVV3kXkZQPkNG8M6SVpSRqdmaxVtGv
