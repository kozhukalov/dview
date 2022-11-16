import os
import logging
import struct
from flask import json
import numpy as np
from dview_server.decoders.afi import AFI

logger = logging.getLogger(__name__)

SYNC_WORD = 0x2A502A50              # ADC64 & TQDC2
SYNC_WORD_TIME = 0x3f60b8a8          # ADC64
CHANNEL_NUMBER = 64

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

class ADC64VEv2(AFI):
    def __init__(self):
        super(AFI, self).__init__()
        

    def read_event(self,event=1):
        msg = "Reading metadata for Event#{:d}".format(event)
        logger.info(msg)

        event_index_list = self.fileIndex[self.fileIndex['ev']==event]
        if (len(event_index_list)==0):
            msg = "Event# {:d} not found".format(event)
            logger.error(msg)
            raise Exception(msg)

        pos = event_index_list[0]['po']

        dev_list = []
        data = dict()
        time_header = dict()
        event_header = dict()
        device_header = dict()
        mstream_time_header = dict()
        mstream_time_block = dict()
        adc_header = dict()

        wave_dev_list = []
        buffer = []
        time_header_size = 4*4
        mstream_time_header_size = 4    # 8 bytes - time header
        mstream_time_block_size = 4*4    # 8 bytes - mstream header size
        with open(self.dataFile, mode='rb') as f:
            # Readout event TIME header
            f.seek(pos - time_header_size)
            time_header.update({"sync_word": struct.unpack('<I', f.read(word_size))[0]})
            time_header.update({"length": struct.unpack('<I', f.read(word_size))[0]})
            time_header.update({"time_lo": struct.unpack('<I', f.read(word_size))[0]})
            time_header.update({"time_hi": struct.unpack('<I', f.read(word_size))[0]})
            if (time_header['sync_word'] == SYNC_WORD_TIME):
                time_header['ntp_ms']  = time_header['time_lo']
                time_header['ntp_ms'] |= (time_header['time_hi'] << 32)
            f.seek(pos)
            event_header.update({"sync_word": struct.unpack('<I', f.read(word_size))[0]})
            event_header.update({"size": struct.unpack('<I', f.read(word_size))[0]})
            event_header.update({"event_abs": struct.unpack('<I', f.read(word_size))[0]})
            event_size = int(event_header['size']/4)
            for i in range(event_size):
                buffer.append(f.read(word_size))

        offset = 0
        # Read out devices
        while (offset != event_size):
            device_header.update({'devsn': struct.unpack('<I', buffer[offset])[0]})
            offset += 1
            device_header.update({'id': (struct.unpack('<I', buffer[offset])[0] & 0xFF000000)>>24})
            device_header.update({'length': (struct.unpack('<I', buffer[offset])[0] & 0x00FFFFFF)})
            offset += 1

            mstream_time_header.update({ 'subtype': (struct.unpack('<I', buffer[offset])[0] & 0xFF000000) >> 24 })
            mstream_time_header.update({ 'length': (struct.unpack('<I', buffer[offset])[0] & 0x0000FFFF) })
            offset += 1

            if (mstream_time_header['length'] == 0):
                msg = "Event#{:d} is corrupted. MStream block has zero length".format(event)
                logger.error(msg)
                raise Exception(msg)

            mstream_time_block.update({ 'taisec': struct.unpack('<I', buffer[offset])[0] })
            offset += 1
            mstream_time_block.update({ 'tainsec': (struct.unpack('<I', buffer[offset])[0] & 0xFFFFFFFC) >> 2 })
            mstream_time_block.update({ 'taiflags': (struct.unpack('<I', buffer[offset])[0] & 0x3) })
            offset +=1
            mstream_time_block.update({ 'chlo': struct.unpack('<I', buffer[offset])[0] })
            offset +=1
            mstream_time_block.update({ 'chup': struct.unpack('<I', buffer[offset])[0] })
            offset +=1

            mstream_time_block['ach_bits'] = mstream_time_block['chlo']
            mstream_time_block['ach_bits'] |= (mstream_time_block['chup'] << 32)
            active_channels = [int(i) for i,ch in enumerate(np.binary_repr(mstream_time_block['ach_bits'], CHANNEL_NUMBER))]

            mstream_data_block_size = int((device_header['length']-mstream_time_header_size-mstream_time_block_size)/word_size)
            moffset = 0
            mstream_data_block_list = []
            wave_list = []

            # Read out MStreams
            while (moffset != mstream_data_block_size):
                # ADC Data type
                adc_header.update({ 'ch': (struct.unpack('<I', buffer[moffset+offset])[0] & 0xFF000000) >> 24 })
                adc_header.update({ 'length': (struct.unpack('<I', buffer[moffset+offset])[0] & 0x00FFFFFC)  >> 2 })
                adc_header.update({ 'type': (struct.unpack('<I', buffer[moffset+offset])[0] & 0x3) })
                moffset +=1
                adc_header.update({ 'tslo': (struct.unpack('<I', buffer[moffset+offset])[0]) })
                moffset +=1
                adc_header.update({ 'tsup': (struct.unpack('<I', buffer[moffset+offset])[0]) })
                moffset +=1
                ch = adc_header['ch']
                sn = int((adc_header['length']-2)*2)  # Number of samples
                waveform = []
                for s in range(int(sn/2)):
                    ind = moffset + offset + s
                    waveform.append( int(np.int16((struct.unpack('<I', buffer[ind])[0] & 0xFFFF0000) >> 16)) )
                    waveform.append( int(np.int16(struct.unpack('<I', buffer[ind])[0] & 0xFFFF)) )
                #end of loop over samples
                wave_list.append({'devsn':device_header['devsn'],'ch': ch,'wf': waveform})
                moffset += int(sn/2)
                mstream_data_block_list.append({'mstream_data_header': dict(adc_header)})
            ##end of loop over mstream data block
            data.update({'device_header': device_header})
            data.update({'mstream_header': mstream_time_header})
            data.update({'mstream_data': mstream_data_block_list})
            data.update({'sample_number': sn})
            data.update({'active_channels': active_channels})
            dev_list.append({'device': device_header['devsn'], 'data': data})
            meta = dict({"event_number": event,'event_header':event_header,'data':dev_list})
            # Add waveforms
            wave_dev_list.append({'device': device_header['devsn'], 'data': wave_list})
            offset += int((device_header['length']-mstream_time_header_size-mstream_time_block_size)/word_size)
        ##end of loop over devices
        data = dict({'meta': meta, 'data': wave_dev_list})        
        return data