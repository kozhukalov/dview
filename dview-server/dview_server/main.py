import click
import yaml
from flask import Flask, render_template,request, redirect, jsonify, send_from_directory, json

from dview_server.api import APP

from dview_server.web.controller.main import Main
from dview_server.web.controller.page_not_found import PageNotFound

@APP.route('/')
def main():
    page = request.args.get('opt')

    if (page == 'main'):
        init = Main()
    elif (page == '404'):
        init = PageNotFound()
    else:
        init = Main()
    return init.GetBody(APP.config['USER'])


@APP.route('/read_json_files')
def read_json_files():
    return jsonify('ok')


@click.group()
def cli():
    pass


@cli.command()
@click.option("--host", help="server host", envvar="HOST")
@click.option("--port", type=int, help="server port", envvar="PORT")
@click.option("-c", "--config", "config_file",
              required=True, help="config file")
def serve(host, port,config_file):
    try:
        with open(config_file, "r",encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
    except FileNotFoundError:
        msg = 'No such file or directory: ' + config_file
        print(msg)
        return
    cfg.update({'CONFIG_FILE_PATH_NAME' : config_file})
    APP.config.update({'USER' : cfg})
    APP.static_folder = APP.root_path + APP.config['USER']['DEF_DIR_VIEW'] + 'static'
    APP.template_folder = APP.root_path + APP.config['USER']['DEF_DIR_VIEW'] + 'templates'
    if not (host is None):
        cfg['DEF_HOST'] = host
    if not (port is None):
        cfg['DEF_PORT'] = port
    APP.run(host=cfg['DEF_HOST'], port=cfg['DEF_PORT'], debug=True)
