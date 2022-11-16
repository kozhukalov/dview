
import logging
import struct
import os
import numpy as np
from flask import json

logger = logging.getLogger(__name__)

# To add new device
# Please register your new API class here:
from dview_server.decoders.adc64ve_v2 import ADC64VEv2
from dview_server.decoders.tqdc16vs import TQDC16VS

ClASS_DICT = dict({'0xdf':ADC64VEv2,'0xd6':TQDC16VS})

class Controller():
    def __init__(self,data_file):
        self.devID = None
        self.dataFile = data_file        
        self.set_data_file(data_file)


    # !!! must be reimplemented to support other devices
    # These function determines which type of device will be processed
    def look_for_device_id(self,file):    
        SYNC_WORD = 0x2A502A50      # ADC64 & TQDC2
        word_size = 4   # in bytes    
        event = 0
        dt = np.dtype([('ev', np.int32),('po', np.int64),('sn', np.int32),('size', np.int32)])
        content = []
        try:
            with open(file, mode='rb') as f:
                byte_content = 1
                while byte_content:
                    byte_content = f.read(word_size)
                    byte_content_size = (byte_content.__sizeof__()-5)/8
                    if (byte_content_size < word_size):
                        break
                    word = struct.unpack('<I', byte_content)[0]
                    # print(word)
                    if (word == SYNC_WORD):
                        event += 1
                        pos = f.tell()-word_size*1
                        event_header = struct.unpack('<III', f.read(word_size*3))
                        event_size = event_header[0]
                        # event_num = event_header[1]   # absolute event number from data
                        devsn = event_header[2]
                        content.append((event,pos,devsn,event_size))
                        # print(event_header)
                        f.seek(pos+event_size)
        except IOError:
            msg = 'Error: Could not open the file: ' + self.dataFile
            logger.error(msg)
            raise Exception(msg)
        self.eventNum = event
        fileIndex = np.array(content,dtype=dt)

        dev = []
        device_id = 0
        unique = np.unique(fileIndex['size'])
        if (len(unique)==0):
            return 0
        max_size = max(unique)
        pos = fileIndex[fileIndex['size']==max_size][0]['po']
        event_header_size = 3*4     # 12 bytes - event header
        device_header_size = 2*4    # 8 bytes - device header
        with open(file, mode='rb') as f:
            f.seek(pos)
            event_header = struct.unpack('<III', f.read(event_header_size))
            end = event_header[1]
            while (end != 0):
                device_header = struct.unpack('<II', f.read(device_header_size))
                device_id = (device_header[1] & 0xFF000000) >> 24
                device_payload_size = (device_header[1] & 0x00FFFFFF)
                dev.append(device_header[0])
                f.seek(f.tell()+device_payload_size)
                end -= (device_payload_size + device_header_size)
        if (len(dev) == 0):
            msg = 'Devices are not found in ' + self.dataFile
            logger.error(msg)
            raise Exception(msg)
        self.devID = str(hex(device_id))    # form key


    def set_data_file(self,data_file):
        logger.info("Set data file: " + data_file)
        if (os.path.isfile(data_file) == False):
            msg = 'Error: Could not open the file: ' + data_file
            logger.error(msg)
            raise Exception(msg)
        self.dataFile = data_file
        self.look_for_device_id(data_file)
        self.file_indexation(data_file)


    def load_json_template(self,path,filename):
        template_path = os.path.join(path, "static", filename)
        data = json.load(open(template_path))
        return data


    def save_json_file(self,path,filename,data):
        dst = "{:s}/static/{:s}".format(path,filename)
        with open(dst, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)


    def form_single_wf_buffer(self,event_number,event_data):
        DEF_WF_TEMPLATE_JSON_PATH = os.path.dirname(
                                        os.path.realpath(__file__)
                                    ).replace('/decoders','') +\
                                    '/web/view'
        sn = event_data['meta']['data'][0]['data']['sample_number']   # number of samples for the 1st device
        single_wf_template = self.load_json_template(DEF_WF_TEMPLATE_JSON_PATH,'wave_t.json')
        single_wf_template['fNpoints'] = sn
        fX = [s for s in range(sn)]
        single_wf_template['fX'] = fX
        tgraphs_json = dict()
        for d in event_data['data']:
            for ch_data in d['data']:
                fName = "Device_{:s}_CH{:02d}".format(str(hex(ch_data['devsn'])),ch_data['ch'])
                single_wf_template['fName'] = fName
                single_wf_template['fTitle'] = "Single waveform [Dev.: {:s} CH{:02d} Event#{:d}]".format(str(hex(ch_data['devsn'])),\
                                                                                                            ch_data['ch'],\
                                                                                                            event_number)
                single_wf_template['fY'] = ch_data['wf']
                # print(ch_data['ch'],ch_data['wf'][:5])
                tgraphs_json.update({fName: dict(single_wf_template)})
        self.save_json_file(DEF_WF_TEMPLATE_JSON_PATH,'single_wf.json',tgraphs_json)

    # These methonds will be redefined by appropriate device class
    def file_indexation(self, data_file):
        dev_class = ClASS_DICT[self.devID]
        return dev_class.file_indexation(dev_class,data_file)

    def get_devices(self):
        dev_class = ClASS_DICT[self.devID]
        return dev_class.get_devices(dev_class)

    def get_event_number(self):
        dev_class = ClASS_DICT[self.devID]
        return dev_class.get_event_number(dev_class)

    def read_event(self, event):
        dev_class = ClASS_DICT[self.devID]
        return dev_class.read_event(dev_class,event)