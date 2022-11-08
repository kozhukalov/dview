import click
from dview_rclient import api

@click.group()
def rclient():
    pass


@rclient.command()
@click.option("-c", "--config", "config_file", required=True, help="config file")
def server_status(config_file):
    res = api.get_server_status(config_file)
    print(f"Server status: {res} [True - server is up, False - server is down]")


@rclient.command()
@click.option("-c", "--config", "config_file", required=True, help="config file")
@click.option("-d", "--data", "data_file", required=True, help="input remote data file")
@click.option("-e", "--event", "event", required=True, help="event number")
def read_meta(config_file,data_file,event):
    res = api.read_meta(config_file,data_file,event)
    if (res['status'] == False):
        print(res['message'])
        return

    meta = res['data']['meta']
    if (meta != None):
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
