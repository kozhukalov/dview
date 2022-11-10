# Abstract class of main controller
from abc import ABC, abstractmethod
from flask import render_template

class AController(ABC):
    def __init__(self):
        pass


    def Render(self,template,data):
        return render_template(str.lower(template)+'.html',data=data)


    @abstractmethod
    def GetBody(self,cfg):
        pass