import requests
from requests.auth import HTTPBasicAuth
import json
import datetime
import sys

# parse arguments
file_path = sys.argv[1]
jamf_domain = sys.argv[2]
username = sys.argv[3]
password = sys.argv[4]

with open(file_path, "r") as config_file:
    dept_file = json.loads(config_file.read())

print(jamf_domain)

url = f"https://{jamf_domain}.jamfcloud.com/"
config_file_dept_names = []
config_file_dept_ids = []


#### functions region ####

def jamf_token(username, password, url):
    endpoint = "uapi/auth/tokens"
    new_url = url + endpoint
    resp = requests.post(url=new_url, auth=HTTPBasicAuth(username, password))
    resp = resp.json()
    token = resp["token"]
    return token

def add_departments(departments, token):
    endpoint = "uapi/v1/departments"
    current_url = url + endpoint
    headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": "Bearer " + token
            }
    current_departments = get_departments(token)
    current_dept_names = [i['name'] for i in current_departments]
    departments_to_create = [i for i in departments if i not in current_dept_names]
    for department in departments_to_create:
        data = {"name": department}
        response = requests.request("POST", url=current_url,json=data, headers=headers)
        print(response.text)

def get_departments(token):
    endpoint = "uapi/v1/departments"
    current_url = url + endpoint
    headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": "Bearer " + token
            }
    response = requests.get(url=current_url, headers=headers )
    return response.json()['results']

def get_dept_id(name, token):
    current_departments = get_departments(token)
    for dept in current_departments:
        if dept["name"] == name:
            id = dept["id"]
            break
    return id

def update_department(old_name, new_name, token):
    id = get_dept_id(old_name, token)
    endpoint = "uapi/v1/departments/"
    current_url = url + endpoint + id
    headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": "Bearer " + token
            }
    data = {"name": new_name}
    requests.put(url=current_url, headers=headers, json=data)

def delete_department(department_name, token):
    try:
        id = get_dept_id(department_name,token)
    except:
        print("This department does not exist, please try again with a valid department name")
        return
    endpoint = "uapi/v1/departments/"
    current_url = url + endpoint + id
    headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": "Bearer " + token
    }
    requests.delete(url=current_url, headers=headers)
    print(get_departments(token))

def get_department_history(department_name, token):
    try:
        id = get_dept_id(department_name, token)
    except:
        print("This department does not exist, please try again with a valid department name")
        return
    endpoint = "uapi/v1/departments/"
    current_url = url + endpoint + id + "/history"
    headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": "Bearer " + token
    }
    resp = requests.get(url=current_url, headers=headers)
    return resp.json()["results"]
    
def get_all_departmant_history(token):
    all_depts = get_departments(token)
    all_dept_history = {}
    for dept in all_depts:
        dept_name = dept["name"]
        hist = get_department_history(dept_name, token)
        dept_history_items = []
        for item in hist:
            new_item = {}
            dept_id = item["id"]
            ChangedBy = item["username"]
            ChangeType = item["note"]
            date_and_time = datetime.datetime.strptime((item["date"][:-1]), '%Y-%m-%dT%H:%M:%S.%f')
            date_and_time = datetime.datetime.strftime(date_and_time, " %y/%m/%d - %H:%M:%S")
            new_item.update({"ID": dept_id, "Name": dept_name , "Changed By": ChangedBy, "Change Type": ChangeType, "Date": date_and_time })
            dept_history_items.append(new_item)
        all_dept_history.update({dept_name: dept_history_items})
    return all_dept_history

#### End functions region ####
########################################################
#### Code region ####

tok = jamf_token(username, password, url)

for dept in dept_file["departments"]:
    config_file_dept_names.append(dept["name"])
    try:
        config_file_dept_ids.append(dept["id"])
    except:
        continue

current_jamf_depts = get_departments(tok)
current_dept_names = [i['name'] for i in current_jamf_depts]
current_dept_ids = [i['id'] for i in current_jamf_depts]

add_departments(config_file_dept_names, tok)

for dept in current_dept_names:
    if dept not in config_file_dept_names:
        delete_department(dept, tok)

for dept in current_jamf_depts:
    for config_dept in dept_file["departments"]:
        if 'id' not in config_dept:
            continue
        if config_dept["id"] == dept["id"]:
            if config_dept["name"] != dept["name"]:
                update_department(dept["name", config_dept["name"], tok])


all_departments = get_all_departmant_history(tok)
departments_history_json = {"logs": []}

for deptName in all_departments:
     for history_item in all_departments[deptName]:
         log_item = {"Department ID": f"{history_item['ID']}", "Department Name": f"{history_item['Name']}","User Making Change": f"{history_item['Changed By']}", "Type of Change": f"{history_item['Change Type']}", "Change date": f"{history_item['Date']}"}
         departments_history_json["logs"].append(log_item)


from datetime import datetime
date = datetime.now().strftime("%Y-%m-%d")

print(json.dumps(departments_history_json, indent=4, sort_keys=True))


#### End Code region ####


