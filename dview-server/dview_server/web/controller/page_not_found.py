# PageNotFound controller class
from flask import Flask, render_template,request, redirect, jsonify
from dview_server.web.controller.acontroller import AController

import logging
logger = logging.getLogger(__name__)

class PageNotFound(AController):
    def __init__(self):
        super(AController, self).__init__()


    def GetBody(self):
        return render_template('page_not_found.html')