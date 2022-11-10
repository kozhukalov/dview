import os
import logging
import struct
from flask import json
import numpy as np

logger = logging.getLogger(__name__)

SYNC_WORD = 0x2A502A50              # ADC64 & TQDC2
TQDC_START_SYNC_WORD = 0x72617453   # Start/Stop Run Block
TQDC_STOP_SYNC_WORD = 0x706F7453    # Start/Stop Run Block
TQDC_RUN_NUMBER_RECORD_SYNC_WORD = 0x236E7552
TQDC_RUN_INDEX_RECORD_SYNC_WORD = 0x78646E49

DEF_WF_TEMPLATE_JSON_PATH = '/home/tao/soft/dview/dview-server/dview_server/web/view'

word_size = 4   # in bytes

# Logger settings
# add filemode="w" to overwrite
# logging.basicConfig(level=logging.INFO, filemode="w")
# logger = logging.getLogger(__name__)
# fh = logging.FileHandler('tqdc.log')
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# fh.setFormatter(formatter)
# logger.addHandler(fh)

class TQDCDecoder:
    def __init__(self):
        self.eventNum = None
        self.dataFile = None
        self.fileIndex = None
        self.devices = None
        self.metaData = dict()
        self.eventData = dict()


    def get_event_number(self):
        return self.eventNum


    def get_data_file(self):
        return self.dataFile


    def set_data_file(self,data_file):
        logger.info("Set data file: " + data_file)
        if (os.path.isfile(data_file) == False):
            msg = 'Error: Could not open the file: ' + data_file
            logger.error(msg)
            raise Exception(msg)
        self.dataFile = data_file


    def get_devices(self):
        return self.devices


    def load_json_template(self,path,filename):
        print(path,filename)
        template_path = os.path.join(path, "static", filename)
        data = json.load(open(template_path))
        return data


    def save_json_file(self,path,filename,data):
        dst = "{:s}/static/{:s}".format(path,filename)
        with open(dst, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)


    def form_single_wf_buffer(self,event_number,event_data):
        sn = event_data['meta']['data'][0]['data']['sample_number']   # number of samples for the 1st device
        single_wf_template = self.load_json_template(DEF_WF_TEMPLATE_JSON_PATH,'wave_t.json')
        single_wf_template['fNpoints'] = sn
        fX = [s for s in range(sn)]
        single_wf_template['fX'] = fX
        tgraphs_json = dict()
        for d in event_data['data']:
            print(d['device'])
            for ch_data in d['data']:
                fName = "Device_{:s}_CH{:02d}".format(str(hex(ch_data['devsn'])),ch_data['ch'])
                single_wf_template['fName'] = fName
                single_wf_template['fTitle'] = "Single waveform [Dev.: {:s} CH{:02d} Event#{:d}]".format(str(hex(ch_data['devsn'])),\
                                                                                                            ch_data['ch'],\
                                                                                                            event_number)
                single_wf_template['fY'] = ch_data['wf']
                print(single_wf_template['fName'],single_wf_template['fNpoints'])
                tgraphs_json.update({fName: dict(single_wf_template)})
        self.save_json_file(DEF_WF_TEMPLATE_JSON_PATH,'single_wf.json',tgraphs_json)



    def file_indexation(self):
        event = 0
        dt = np.dtype([('ev', np.int32),('po', np.int64), ('size', np.int32)])
        content = []
        try:
            with open(self.dataFile, mode='rb') as f:
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
                        content.append((event,pos,event_size))
                        # print(event_header)
                        f.seek(pos+event_size)
        except IOError:
            msg = 'Error: Could not open the file: ' + self.dataFile
            logger.error(msg)
            raise Exception(msg)
        self.eventNum = event
        self.fileIndex = np.array(content,dtype=dt)
        self.devices = self.look_for_devices()
        if (self.devices == 0):
            msg = 'Devices are not found in ' + self.dataFile
            logger.error(msg)
            raise Exception(msg)



    def look_for_devices(self):
        dev = []
        unique = np.unique(self.fileIndex['size'])
        if (len(unique)==0):
            return 0
        max_size = max(unique)
        pos = self.fileIndex[self.fileIndex['size']==max_size][0]['po']
        event_header_size = 3*4     # 12 bytes - event header
        device_header_size = 2*4    # 8 bytes - device header
        with open(self.dataFile, mode='rb') as f:
            f.seek(pos)
            event_header = struct.unpack('<III', f.read(event_header_size))
            end = event_header[1]
            while (end != 0):
                device_header = struct.unpack('<II', f.read(device_header_size))
                device_payload_size = (device_header[1] & 0x00FFFFFF)
                dev.append(device_header[0])
                f.seek(f.tell()+device_payload_size)
                end -= (device_payload_size + device_header_size)
        return dev


    def read_event(self,event=1):
        msg = "Reading metadata for Event#{:d}".format(event)
        logger.info(msg)
        try:
            pos = self.fileIndex[self.fileIndex['ev']==event][0]['po']
        except IndexError:
            msg = "Event# {:d} not found".format(event)
            logger.error(msg)
            raise Exception(msg)

        # event_header_size = 4*3
        dev_list = []
        data = dict()
        event_header = dict()
        device_header = dict()
        mstream_header = dict()
        mstream_data_block_header = dict()
        tdc_event_header = dict()
        tdc_event_trailer = dict()
        tdc_leading_edge = dict()
        tdc_trailing_edge = dict()
        tdc_err = dict()
        adc_header = dict()
        wave_dev_list = []
        buffer = []
        with open(self.dataFile, mode='rb') as f:
            f.seek(pos)
            event_header.update({"sync_word": struct.unpack('<I', f.read(word_size))[0]})
            event_header.update({"size": struct.unpack('<I', f.read(word_size))[0]})
            event_header.update({"event_abs": struct.unpack('<I', f.read(word_size))[0]})
            event_size = int(event_header['size']/4)
            for i in range(event_size):
                buffer.append(f.read(word_size))

        mstream_time_header_size = 2*4    # 8 bytes - time header
        offset = 0
        # Read out devices
        while (offset != event_size):
            device_header.update({'devsn': struct.unpack('<I', buffer[offset])[0]})
            offset += 1
            device_header.update({'id': (struct.unpack('<I', buffer[offset])[0] & 0xFF000000)>>24})
            device_header.update({'length': (struct.unpack('<I', buffer[offset])[0] & 0x00FFFFFF)})
            offset += 1

            device_block_size = int(device_header['length']/word_size)
            moffset = 0
            # Read out MStreams
            while (moffset != device_block_size):
                mstream_header.update({ 'subtype': (struct.unpack('<I', buffer[moffset+offset])[0] & 0xFF000000) >> 24 })
                mstream_header.update({ 'length': (struct.unpack('<I', buffer[moffset+offset])[0] & 0x0000FFFF) })
                moffset += 1
                mstream_header.update({ 'taisec': struct.unpack('<I', buffer[moffset+offset])[0] })
                moffset += 1
                mstream_header.update({ 'tainsec': (struct.unpack('<I', buffer[moffset+offset])[0] & 0xFFFFFFFC) >> 2 })
                mstream_header.update({ 'taiflags': (struct.unpack('<I', buffer[moffset+offset])[0] & 0x3) })
                moffset +=1

                if (mstream_header['length'] == 0):
                    msg = "Event#{:d} is corrupted. MStream block has zero length".format(event)
                    logger.error(msg)
                    raise Exception(msg)

                if (mstream_header['subtype'] == 0):
                    doffset = 0
                    mstream_data_size = int((mstream_header['length'] - mstream_time_header_size)/word_size)
                    active_channels = []
                    mstream_data_block_list = []
                    wave_list = []
                    # MStream subtype 0
                    while (doffset != mstream_data_size):
                        mstream_data_block_header.update({ 'type': (struct.unpack('<I', buffer[doffset+moffset+offset])[0] & 0xF0000000) >> 28 })
                        mstream_data_block_header.update({ 'ch': (struct.unpack('<I', buffer[doffset+moffset+offset])[0] & 0xF000000)  >> 24 })
                        mstream_data_block_header.update({ 'spec': (struct.unpack('<I', buffer[doffset+moffset+offset])[0] & 0x70000)    >> 16 })
                        mstream_data_block_header.update({ 'length': (struct.unpack('<I', buffer[doffset+moffset+offset])[0] & 0xFFFF) })
                        doffset += 1

                        if (mstream_data_block_header['type'] == 0):
                            # TDC Data type
                            data_size = mstream_data_block_header['length']/4;
                            device_data_header = dict()
                            while (data_size != 0):
                                tdc_data_type = (struct.unpack('<I', buffer[doffset+moffset+offset])[0] & 0xF0000000) >> 28
                                if (tdc_data_type == 2):
                                    # Decode TDC event header
                                    tdc_event_header.update({ 'timestamp': (struct.unpack('<I', buffer[doffset+moffset+offset])[0] & 0xFFF) })
                                    tdc_event_header.update({ 'evnum': (struct.unpack('<I', buffer[doffset+moffset+offset])[0] & 0xFFF000) >> 12 })
                                    tdc_event_header.update({ 'id': (struct.unpack('<I', buffer[doffset+moffset+offset])[0] & 0xF000000) >> 24 })
                                    tdc_event_header.update({ 'n': (struct.unpack('<I', buffer[doffset+moffset+offset])[0] & 0xF0000000) >> 28 })
                                    doffset += 1
                                    device_data_header = tdc_event_header
                                elif (tdc_data_type == 3):
                                    # Decode TDC event trailer
                                    tdc_event_trailer.update({ 'wcount': (struct.unpack('<I', buffer[doffset+moffset+offset])[0] & 0xFFF) })
                                    tdc_event_trailer.update({ 'evnum': (struct.unpack('<I', buffer[doffset+moffset+offset])[0] & 0xFFF000) >> 12 })
                                    tdc_event_trailer.update({ 'id': (struct.unpack('<I', buffer[doffset+moffset+offset])[0] & 0xF000000) >> 24 })
                                    tdc_event_trailer.update({ 'n': (struct.unpack('<I', buffer[doffset+moffset+offset])[0] & 0xF0000000) >> 28 })
                                    doffset += 1
                                    device_data_header = tdc_event_trailer
                                elif (tdc_data_type == 4):
                                    # Decode TDC data leading edge
                                    tdc_leading_edge.update({ 'rcdata': (struct.unpack('<I', buffer[doffset+moffset+offset])[0] & 0x3) })
                                    tdc_leading_edge.update({ 'ledge': (struct.unpack('<I', buffer[doffset+moffset+offset])[0] & 0x1FFFFC) >> 2 })
                                    tdc_leading_edge.update({ 'ch': (struct.unpack('<I', buffer[doffset+moffset+offset])[0] & 0x1E00000) >> 21 })
                                    tdc_leading_edge.update({ 'n': (struct.unpack('<I', buffer[doffset+moffset+offset])[0] & 0xF0000000) >> 28 })
                                    doffset += 1
                                    device_data_header = tdc_leading_edge
                                elif (tdc_data_type == 5):
                                    # Decode TDC data trailing edge
                                    tdc_trailing_edge.update({ 'rcdata': (struct.unpack('<I', buffer[doffset+moffset+offset])[0] & 0x3) })
                                    tdc_trailing_edge.update({ 'tedge': (struct.unpack('<I', buffer[doffset+moffset+offset])[0] & 0x1FFFFC) >> 2 })
                                    tdc_trailing_edge.update({ 'ch': (struct.unpack('<I', buffer[doffset+moffset+offset])[0] & 0x1E00000) >> 21 })
                                    tdc_trailing_edge.update({ 'n': (struct.unpack('<I', buffer[doffset+moffset+offset])[0] & 0xF0000000) >> 28 })
                                    doffset += 1
                                    device_data_header = tdc_trailing_edge
                                elif (tdc_data_type == 6):
                                    # Decode TDC error
                                    tdc_err.update({ 'err': (struct.unpack('<I', buffer[doffset+moffset+offset])[0] & 0x7FFF) })
                                    tdc_err.update({ 'id': (struct.unpack('<I', buffer[doffset+moffset+offset])[0] & 0xF000000)  >> 24 })
                                    tdc_err.update({ 'n': (struct.unpack('<I', buffer[doffset+moffset+offset])[0] & 0xF0000000) >> 28 })
                                    doffset += 1
                                    device_data_header = tdc_err
                                data_size -= 1
                        elif (mstream_data_block_header['type'] == 1):
                            # ADC Data type
                            adc_header.update({ 'timestamp': (struct.unpack('<I', buffer[doffset+moffset+offset])[0] & 0xFFFF) })
                            adc_header.update({ 'length': (struct.unpack('<I', buffer[doffset+moffset+offset])[0] & 0xFFFF0000) >> 16 })
                            doffset +=1
                            ch = mstream_data_block_header['ch']
                            active_channels.append(ch)
                            sn = int((adc_header['length']/4)*2)       # Number of samples
                            device_data_header = adc_header
                            waveform = []
                            for s in range(int(sn/2)):
                                ind = doffset + moffset + offset + s
                                waveform.append( struct.unpack('<I', buffer[ind])[0] & 0xFFFF )
                                waveform.append( (struct.unpack('<I', buffer[ind])[0] & 0xFFFF0000) >> 16 )
                            ##end of loop over samples
                            wave_list.append({'devsn':device_header['devsn'],'ch': ch,'wf': waveform})
                            doffset += int(sn/2)
                        ##end of data type switch
                        mstream_data_block_list.append({'mstream_data_header': dict(mstream_data_block_header),\
                                                        'device_data_header':device_data_header})
                elif (mstream_header['subtype'] == 1):
                    # there is no data for TQDC
                    pass
                ##end of subtype switch
                moffset += int((mstream_header['length'] - mstream_time_header_size)/word_size)
            ##end of loop over mstreams
            data.update({'device_header':device_header})
            data.update({'mstream_header':mstream_header})
            data.update({'mstream_data':mstream_data_block_list})
            data.update({'sample_number': sn})
            data.update({'active_channels': active_channels})
            dev_list.append({'device': device_header['devsn'], 'data': data})
            self.metaData.update({"event_number": event,'event_header':event_header,'data':dev_list})
            # Add waveforms
            wave_dev_list.append({'device': device_header['devsn'], 'data': wave_list})

            offset += int(device_header['length']/word_size)
        ##end of loop over devices
        self.eventData.update({'meta': self.metaData, 'data': wave_dev_list})
        # generate json buffer file for web interface
        self.form_single_wf_buffer(event,self.eventData)
        return self.eventData