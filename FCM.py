import requests

url = 'https://fcm.googleapis.com/fcm/send'
headers = {
    'Authorization': 'key=<AAAAp90srbk:APA91bFjmA4aLmTxRTRNOdzxxVJIgyQUbOI-GpYX6TEJ8bj7_ClIPSRHJQBEmIO_GNV7rgPEmPo1iGqv4mF0rWM9sAI1qIslJ4TxRdHOsRhPwWYsN0CB2Cd28RRbmBxx61jckcHu4Rlx>',
    'Content-Type': 'application/json'
}
data = {
    'to': '<device-token>',
    'notification': {
        'title': 'New Message',
        'body': 'Hello from Python!'
    }
}

response = requests.post(url, headers=headers, json=data)

print(response.json())
