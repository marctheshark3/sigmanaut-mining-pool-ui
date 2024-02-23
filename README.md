# sigma-dashboard

Please note this repo is a work in progress

## Dependency Installation
1. You may need `chmod +x <filename>` as needed to allow these script to be executable
    1. `chmod +x scripts/install_dependencies.sh`
    2. `chmod +x scripts/run_app.sh`
       
2. in a terminal run `scripts/install_dependencies.sh`

## Configuration (recommended)
Put your Mining Address and token of interest, as needed, in the conf.yaml, for example:
```yaml
user_defined:
    wallet: '9eZPTmn8zp5GJ7KZwTo8cEuxNdezWaY3hBbLeWid7EAZedzb9tD'
    token_id: '9f087ebb5d7baf7eb8f13b742e9a9b5b1b8d78b7a7f84d1f9b9d393f4888d679'
```

## Operation
`scripts/run_app.py`

OR

`python3 app.py user_defined.wallet=9eZPTmn8zp5GJ7KZwTo8cEuxNdezWaY3hBbLeWid7EAZedzb9tD`

This will query your address search to see if you have the token of interest and if it does will print out the description of said token. Otherwise the code will tell you that you do not have said token.
