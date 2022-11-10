# Main controller class
from flask import Flask, render_template,request, redirect, jsonify
from dview_server.web.controller.acontroller import AController

import logging
logger = logging.getLogger(__name__)

class Main(AController):
    def __init__(self):
        super(AController, self).__init__()


    def GetBody(self,cfg):
        # model = super().GetModel(cfg)
        # data =model.get_all_table("main")

        return AController.Render(self,\
                                  self.__class__.__name__,\
                                    data={'opt':'main'})