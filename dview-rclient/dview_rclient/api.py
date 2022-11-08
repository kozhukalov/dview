import yaml
import requests


def get_server_status(config_file):
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
    except FileNotFoundError:
        print('No such file or directory: ',config_file)
        return
    host = cfg["endpoint"] + "/api/server_status"
    try:
        with requests.get(host) as resp:
            message = f"Server status code: {resp.status_code}"
            if resp.status_code != 200:
                return False
    except:
        return False
    return True


def read_meta(config_file,rem_data_file,event):
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
    except FileNotFoundError:
        print('No such file or directory: ',config_file)
        return
    host = cfg["endpoint"] + "/api/read_meta"
    try:
        with requests.post(host,{'data_file':rem_data_file,'event':event}) as resp:
            message = f"Server status code: {resp.status_code}"
            status = True
            if resp.status_code != 200:
                status = False
            return {'message': message,'status': status,'data': resp.json()}
    except BaseException as e:
        status = False
        return {'message': str(e),'status': status}
