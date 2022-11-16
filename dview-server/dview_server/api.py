import logging

from flask import Flask, jsonify
from flask_restful import Resource, Api, reqparse, abort

from dview_server.decoders.controller import Controller

logging.basicConfig(level=logging.INFO)

APP = Flask(__name__)
API = Api(APP)

parser = reqparse.RequestParser()
parser.add_argument("event", type=int)
parser.add_argument("data_file", type=str)

class ReadEvent(Resource):
    def post(self):
        args = parser.parse_args()
        data_file = args["data_file"]
        event = args["event"]
        res = {"message": 'ok', "event_data": None}

        try:
            dev = Controller(data_file)
        except BaseException as e:
            res['message'] = str(e)
            return jsonify(res)

        try:
            res['event_data'] = dev.read_event(event)
        except BaseException as e:
            res['message'] = str(e)
            return jsonify(res)

        # generate json buffer file for web interface
        dev.form_single_wf_buffer(event,res['event_data'])

        return jsonify(res)

class GetEventNumber(Resource):
    def post(self):
        args = parser.parse_args()
        data_file = args["data_file"]
        res = {"message": 'ok', "event_number": None}

        try:
            dev = Controller(data_file)
        except BaseException as e:
            res['message'] = str(e)
            return jsonify(res)

        try:
            res['event_number'] = dev.get_event_number()
        except BaseException as e:
            res['message'] = str(e)
            return jsonify(res)
        return jsonify(res)


class GetDevices(Resource):
    def post(self):
        args = parser.parse_args()
        data_file = args["data_file"]
        res = {"message": 'ok', "devices": None}

        try:
            dev = Controller(data_file)
        except BaseException as e:
            res['message'] = str(e)
            return jsonify(res)

        try:
            res['devices'] = dev.get_devices()
        except BaseException as e:
            res['message'] = str(e)
            return jsonify(res)
        return jsonify(res)

class ServerStatus(Resource):
    def get(self):
        return jsonify({"status": True})

API.add_resource(ServerStatus, '/api/server_status')
API.add_resource(ReadEvent, '/api/read_event')
API.add_resource(GetEventNumber, '/api/get_event_number')
API.add_resource(GetDevices, '/api/get_devices')
