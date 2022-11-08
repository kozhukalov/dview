#!/usr/bin/env python
# encoding: utf-8

from tqdc import TQDCDecoder
# 0x0cd96b60 0x080c635b
adc = TQDCDecoder()
# file = "/home/tao/hddata/test/mpd_-50C_1ch_08sipmsON_10080nsLatency_20220511_154951.dat"
# file = "/home/tao/hddata/test/mpd_20220523_183638.data"
# file = "/home/tao/hddata/test/mpd_20211029_175336.data"
file = '/home/tao/data/tmp_tqdc/20221027/mpd_20221028_171639.data'
adc.set_data_file(file)
adc.file_indexation()
# print("devices: ",adc.get_devices())
nevents = adc.get_event_number()
# print('Number of events: ',nevents)
# print(adc.fileIndex['sn'])
# for ind in adc.fileIndex:
#     print(ind['sn'])

# print(adc.fileIndex)

meta = adc.read_meta(35)
print(meta)

# adc.read_event(35)
