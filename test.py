FIREBASE_API_KEY = "AIzaSyC74w_JCigORyepa_esLkPt-B3HgtI_X3o"
FIREBASE_AUTH_DOMAIN = "mantis-4040b.firebaseapp.com"
FIREBASE_PROJECT_ID = "mantis-4040b"
FIREBASE_STORAGE_BUCKET = "mantis-4040b.appspot.com"
FIREBASE_MESSAGING_SENDER_ID = "1073498457348"
FIREBASE_APP_ID = "1:1073498457348:web:268210e18c8f2cab30fc51"
FIREBASE_MEASUREMENT_ID = "G-7SP8EXFS48"

import requests
from firebase_admin import firestore, initialize_app, credentials
import jwt

certs_url = "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com"
response = requests.get(certs_url)
certs = response.json()

token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjY5NjI5NzU5NmJiNWQ4N2…5jAxNAUkHuBF3I4EMOXq76cmm1v7ARHo7kD_8ylAYCD3MtVUQ"
# Decode the token
# decoded_token = jwt.decode(
#     token, certs, algorithms=["RS256"], audience=FIREBASE_PROJECT_ID
# )
# print(decoded_token)


import requests


def verify_firebase_token(id_token):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={FIREBASE_API_KEY}"
    headers = {"Content-Type": "application/json"}
    body = {"idToken": id_token}

    response = requests.post(url, json=body, headers=headers)
    if response.status_code == 200:
        return response.json()  # Token is valid
    else:
        return None  # Token is invalid



decoded_token = verify_firebase_token(token)
if decoded_token:
    print("Token is valid:", decoded_token)
else:
    print("Invalid token")
