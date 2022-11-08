import logging

from flask import Flask, jsonify
from flask_restful import Resource, Api, reqparse, abort

from dview_server.decoders.tqdc import TQDCDecoder

logging.basicConfig(level=logging.INFO)

APP = Flask(__name__)
API = Api(APP)

parser = reqparse.RequestParser()
parser.add_argument("event", type=int)
parser.add_argument("data_file", type=str)

class ReadMeta(Resource):
    def post(self):
        args = parser.parse_args()
        data_file = args["data_file"]
        event = args["event"]
        res = {"message": 'ok', "meta": None}
        adc = TQDCDecoder()

        try:
            adc.set_data_file(data_file)
        except BaseException as e:
            res['message'] = str(e)
            return jsonify(res)

        try:
            adc.file_indexation()
            res['meta'] = adc.read_meta(event)
        except BaseException as e:
            res['message'] = str(e)
            return jsonify(res)
        return jsonify(res)

class ServerStatus(Resource):
    def get(self):
        return jsonify({"status": True})

API.add_resource(ServerStatus, '/api/server_status')
API.add_resource(ReadMeta, '/api/read_meta')
