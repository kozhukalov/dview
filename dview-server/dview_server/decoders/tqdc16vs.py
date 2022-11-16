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

class TQDC16VS(AFI):
    def __init__(self):
        super(AFI, self).__init__()


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
                                waveform.append( int(np.int16(struct.unpack('<I', buffer[ind])[0] & 0xFFFF)) )
                                waveform.append( int(np.int16((struct.unpack('<I', buffer[ind])[0] & 0xFFFF0000) >> 16)) )
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
            meta = dict({"event_number": event,'event_header':event_header,'data':dev_list})
            # Add waveforms
            wave_dev_list.append({'device': device_header['devsn'], 'data': wave_list})

            offset += int(device_header['length']/word_size)
        ##end of loop over devices
        data = dict({'meta': meta, 'data': wave_dev_list})
        return data