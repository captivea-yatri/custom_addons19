import requests, json

url = "http://localhost:1919/jsonrpc"
db = "odoo19_test2"
username = "test@example.com"
password = "a"
headers = {"Content-Type": "application/json"}

# Login
login = {
    "jsonrpc": "2.0",
    "method": "call",
    "params": {"service": "common", "method": "login", "args": [db, username, password]},
    "id": 1,
}
uid = requests.post(url, data=json.dumps(login), headers=headers).json()["result"]

# Create partner
create = {
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "service": "object",
        "method": "execute_kw",
        "args": [db, uid, password, "sale.order", "search", [[]] ],
    },
    "id": 2,
}
response = requests.post(url, data=json.dumps(create), headers=headers).json()
print(json.dumps(response, indent=4))