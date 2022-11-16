import click
from dview import api

@click.group()
def dview():
    pass


@dview.command()
@click.option("-c", "--config", "config_file", required=True, help="config file")
def server_status(config_file):
    res = api.get_server_status(config_file)
    print(f"Server status: {res} [True - server is up, False - server is down]")


@dview.command()
@click.option("-c", "--config", "config_file", required=True, help="config file")
@click.option("-d", "--data", "data_file", required=True, help="input remote data file")
@click.option("-e", "--event", "event", required=True, help="event number")
def read_meta(config_file,data_file,event):
    res = api.read_event(config_file,data_file,event)
    if (res['status'] == False):
        print(res['message'])
        return

    if (res['data']['event_data'] != None):
        meta = res['data']['event_data']['meta']
        k1 = list(meta.keys())
        print('=== Metadata: ===')
        print(k1[2],' : ',meta[k1[2]])
        print(k1[1],' : ',meta[k1[1]])
        print(k1[0],' : ')
        for dev in meta[k1[0]]:
            print(' device: ',hex(dev['device']))
            data = dev['data']
            k2 = list(data.keys())
            print('  ',k2[0],'    : ',data[k2[0]])
            print('  ',k2[4],'      : ',data[k2[4]])
            print('  ',k2[1],'      : ',data[k2[1]])
            print('  ',k2[3],'     : ',data[k2[3]])
            print('  ',k2[2],' : ')
            for item in data[k2[2]]:
                print('    ',item)
        print('=== ========= ===')
    else:
        print(res['data']['message'])

@dview.command()
@click.option("-c", "--config", "config_file", required=True, help="config file")
@click.option("-d", "--data", "data_file", required=True, help="input remote data file")
@click.option("-e", "--event", "event", required=True, help="event number")
def read_event(config_file,data_file,event):
    res = api.read_event(config_file,data_file,event)
    if (res['status'] == False):
        print(res['message'])
        return

    if (res['data']['event_data'] != None):
        event_data = res['data']['event_data']
        print(event_data)
    else:
        print(res['data']['message'])


@dview.command()
@click.option("-c", "--config", "config_file", required=True, help="config file")
@click.option("-d", "--data", "data_file", required=True, help="input remote data file")
def get_event_number(config_file,data_file):
    res = api.get_event_number(config_file,data_file)
    if (res['status'] == False):
        print(res['message'])
        return
    if (res['data']['event_number'] != None):
        event_number = res['data']['event_number']
        print('Number of events:',event_number)
    else:
        print(res['data']['message'])


@dview.command()
@click.option("-c", "--config", "config_file", required=True, help="config file")
@click.option("-d", "--data", "data_file", required=True, help="input remote data file")
def get_devices(config_file,data_file):
    res = api.get_devices(config_file,data_file)
    if (res['status'] == False):
        print(res['message'])
        return
    if (res['data']['devices'] != None):
        print('List of connected devices:')
        for i,dev in enumerate(res['data']['devices']):
            print('Device#',i+1,':',hex(dev))
    else:
        print(res['data']['message'])