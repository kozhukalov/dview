import logging
import struct
import numpy as np


logger = logging.getLogger(__name__)

SYNC_WORD = 0x2A502A50      # ADC64 & TQDC2
word_size = 4               # in bytes

# Common methods for AFI data formats
class AFI():
    def __init__(self):
        self.eventNum = None
        self.dataFile = None
        self.fileIndex = None
        self.devices = None
        self.devID = None
        print('ADevice')

    
    def get_event_number(self):
        return self.eventNum


    def get_devices(self):
        return self.devices


    def file_indexation(self,data_file):
        self.dataFile = data_file
        event = 0
        dt = np.dtype([('ev', np.int32),('po', np.int64),('sn', np.int32),('size', np.int32)])
        content = []
        try:
            with open(data_file, mode='rb') as f:
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
        self.fileIndex = np.array(content,dtype=dt)
        self.devices = self.look_for_devices(self)
        if (len(self.devices) == 0):
            msg = 'Devices are not found in ' + self.dataFile
            logger.error(msg)
            raise Exception(msg)
        

    def look_for_devices(self):
        file = self.dataFile
        dev = []
        device_id = 0
        unique = np.unique(self.fileIndex['size'])
        if (len(unique)==0):
            return 0
        max_size = max(unique)
        pos = self.fileIndex[self.fileIndex['size']==max_size][0]['po']
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
        self.devID = str(hex(device_id))    # form key
        return dev