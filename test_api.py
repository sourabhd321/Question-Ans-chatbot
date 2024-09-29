import requests

url = "http://127.0.0.1:8000/upload/"

payload = {'questions': '{"question": ["What is AI?", "Explain Machine Learning"]}',
'file': '{"content": "this is test documents."}',
'source': 'json'}
files=[

]
headers = {}

response = requests.request("POST", url, headers=headers, data=payload, files=files)

print(response.text)