import requests
import urllib3
urllib3.disable_warnings()
auth = ('superman', 'Admin123')
# Listet alle Visit Types auf
r = requests.get('https://localhost/openmrs/ws/rest/v1/visittype', auth=auth, verify=False)
for vt in r.json()['results']:
    print(f"Name: {vt['display']} | UUID: {vt['uuid']}")