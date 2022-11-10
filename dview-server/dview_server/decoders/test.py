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

# meta = adc.read_meta(35)
# print(meta)
ch = 12
event_number = 35
path = '/home/tao/soft/dview/dview-server/dview_server/web/view'
template_wf = adc.load_json_template(path,'wave_t.json')
plot = template_wf['fPrimitives']['arr'][1]




# print(plot['fTitle'],plot['fNpoints'])


# print(plot['fX'])




data = adc.read_event(event_number)
adc.form_single_wf_buffer(event_number,data)
exit()

sn = data['meta']['data'][0]['data']['sample_number']   # number of samples for the 1st device
print(data['meta']['data'][0]['data']['sample_number'])
plot['fNpoints'] = 2010
plot['fX'] = [s for s in range(plot['fNpoints'])]

# print(data['meta'])

for d in data['data']:
    print(d['device'])
    for ch_data in d['data']:
        plot['fTitle'] = "Single waveform CH{:02d} [Event#{:d}]".format(ch_data['ch'],event_number)
        plot['fY'] = ch_data['wf']
        wf_filename = "wf_dev_{:s}_ch_{:02d}.json".format(str(hex(ch_data['devsn'])),ch_data['ch'])
        adc.save_json_file(path,wf_filename,template_wf)
#         print(ch_data['devsn'],ch_data['ch'],ch_data['wf'][:5])

# wf = data['data'][0]['data'][0]['wf']
# print(plot['fY'])



# from ROOT import TGraph
# from array import array
# print(TGraph)
# p = TGraph(2010,array('d',plot['fX']),array('d',plot['fY']))
# p.Draw("APL*")
# raw_input()