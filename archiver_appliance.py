# -*- coding: utf-8 -*-
'''
This Python module provides a few functions to manipulate the Archiver Appliance (AA) 
Packages required: python-requests; python-pandas
'''

from __future__ import print_function

import os
import sys
import urllib
#import urllib2
import json
from datetime import datetime
import time
import traceback
import re
import glob
#import subprocess
from collections import OrderedDict as odict

from epicsarchiver import ArchiverAppliance

# get the Archiver FULL hostname: localhost or hostname defined in aa.conf 
try:
    import socket
    localhost = socket.getfqdn()
    archiver = ArchiverAppliance(str(localhost))
    print("{}: {}".format(localhost, archiver.version))
except:
    #traceback.print_exc()
    import ConfigParser
    config = ConfigParser.ConfigParser()
    config.optionxform = str #keep keys as its original
    # user home directory settings will overwrite system config(/etc/...), 
    # system config will overwrite aa.conf in the current working directory
    aa_conf_user = os.path.expanduser('~/aa.conf')
    config.read(['aa.conf', '/etc/default/aa.conf', aa_conf_user])
    aaconfig_dict = {}
    sections = config.sections()
    for section in sections:
        aaconfig_dict[section] = dict(config.items(section))
    if not aaconfig_dict:
        print("Aborted: no aa.conf found or something wrong inside aa.conf")
        sys.exit()

    try:
        archiver = ArchiverAppliance(hostname=str(aaconfig_dict['Settings']['Servername']))
        print(archiver.version)
    except:
        print("Aborted: the Archiver server is not localhost {} and it is not \
correctly set in aa.conf (or /etc/default/aa.conf or {})".format(localhost, aa_conf_user))
        sys.exit()

'''
archiver.abort_pv                       archiver.hostname
archiver.archive_pv                     archiver.identity
archiver.archive_pvs                    archiver.info
archiver.archive_pvs_from_files         archiver.mgmt_url
archiver.data_url                       archiver.pause_pv
archiver.delete_pv                      archiver.pause_rename_resume_pv
archiver.get                            archiver.post
archiver.get_all_expanded_pvs           archiver.rename_pv
archiver.get_all_pvs                    archiver.rename_pvs_from_files
archiver.get_data                       archiver.request
archiver.get_pv_status                  archiver.resume_pv
archiver.get_pv_status_from_files       archiver.session
archiver.get_unarchived_pvs             archiver.update_pv
archiver.get_unarchived_pvs_from_files  archiver.version
'''


def _log_pvs(pvs, file_prefix):
    '''save pvs to a file'''
    timestamp = time.strftime("-%Y%b%d_%H%M%S")
    home_dir = os.path.expanduser("~")
    _file_prefix = str(file_prefix).replace(" ", "-")
    file_name = home_dir + "/" + _file_prefix + str(timestamp)+".txt"
    with open(str(file_name), 'w') as fd:
        if isinstance(pvs[0], unicode):#string
            for pv in pvs:
                fd.write(str(pv) + "\n")
        elif isinstance(pvs[0], odict):
            for pv_dict in pvs:
                for (k, v) in pv_dict.iteritems():
                    fd.write(str(k+":\t")+str(v)+"\n")
                #fd.write("\n")

    print("{} PVs have been written to the file {}".format(len(pvs), file_name))


def _report_pvs(results, desc, sort=True):
    '''report PV names and save them to a file if confirmed'''
    if not results:
        print("No %s\n"%str(desc))
        return

    pvNames=results
    if isinstance(results[0], dict): 
        pvNames = [dic['pvName'] for dic in results]
    if sort:
        pvNames.sort()

    if len(pvNames) > 10:
        pvs_4print=pvNames[:9]
    else:
        pvs_4print=pvNames
    for pv in pvs_4print:
        print(pv)
    print("...\n%d %s\n"%(len(pvNames), str(desc)))

    answer = raw_input("Do you want to write these PVs to a file? Type yes or no: ")
    if (answer.upper() == "YES"):
        _log_pvs(pvNames, desc)

    return pvNames


def get_pvs_from_file(filename):
    with open(filename, "r") as fd:
        lines = fd.readlines()
        pvList = []
        for line in lines:
            if line.startswith("#") or line == "":
            # Remove empty lines and lines that start with "#"
                continue
            pvList.append(str(line).strip())
            
    pvs = set(pvList) # remove duplicated PVs
    print("get %d PVs from %s"%(len(pvs), filename))
    return pvs
    

def get_allPVs(pv="*", regex="*", limit=-1, do_return=False):
    '''get_all_pvs(self, pv=None, regex=None, limit=500)'''
    pvs = archiver.get_all_pvs(pv=pv, regex=regex, limit=limit)
    if do_return:
        return _report_pvs(pvs, "total PVs")
    else:
        _report_pvs(pvs, "total PVs")


def get_waveformPVs(do_log=False, do_return=False):
    '''- Get a list of dicts of waveform PVs that are currently being archived.
    record types could be: waveform, aSub, compress, etc.
    {u'elementCount': u'128', u'samplingperiod': u'1.0', 
    u'pvName': u'BR-TS{EVR:B2A-Out:FPUV3}User-SP', u'samplingmethod': u'MONITOR'}
    '''
    r = archiver.get("/getArchivedWaveforms", params={})
    try:
        results = r.json()
    except:
        results = r.json

    if do_log:
        pvNames = [dic['pvName'] for dic in results]
        pvNames.sort()
        info = get_pvs_file_info(pvNames)
        _log_pvs(info, "waveform file info")

    if do_return:
        return _report_pvs(results, "waveform PVs")
    else:
        _report_pvs(results, "waveform PVs")


def get_storage_rate_report(limit=1000, do_return=False):
    '''- Return a list of dicts of PVs sorted by descending storage rate.
    limit: Limit this report to this many PVs per appliance in the cluster. 
        Optional, if unspecified, there are no limits enforced.
    {u'storageRate_KBperHour': u'16054.3', u'storageRate_MBperDay': u'376.2',     
    u'pvName': u'SR-RF{CFD:2-Cav}E:I', u'storageRate_GBperYear': u'134.1'}
    '''
    r = archiver.get("/getStorageRateReport", params={"limit": limit})  
    try:
        results = r.json()
    except:
        results = r.json
    print(results[0])
    if do_return:
        return _report_pvs(results, "storage rate PVs", sort=False)
    else:
        _report_pvs(results, "storage rate PVs", sort=False)


def get_pvs_file_info(pvs, report_zero_size=True, lts_path='/DATA/lts/ArchiverStore/'):
    '''- Get archived data file name and file size for each pv in pvs
    pv = "SR-RF{CFD:2-Cav}E:I"; relative_path = 'SR/RF/CFD/2/Cav/E/I'
    pb_file: /DATA/lts/ArchiverStore/SR/RF/CFD/2/Cav/E/I:2016.pb
    '''
    pvs_file_info = []
    for pv in pvs:
        pv_file_info = odict()
        total_GB = 0.0
        file_names = []
        relative_path = re.sub('[:{}-]', '/', pv)
        full_path = lts_path + str(relative_path)
        for pb_file in glob.glob(full_path+'*'):
            year = "".join("".join(pb_file.rsplit(full_path+':'))).rsplit('.pb')[0]
            size_GB = round(1.0*os.path.getsize(pb_file)/(1024**3))
            total_GB += size_GB
            #pv_file_info[pv+'('+year+')'] = size_GB # GB per year
            file_names.append(pb_file)

        pv_file_info[pv+'(total)'] = total_GB # total file size (GB) for  pv 
        if report_zero_size:
			if not total_GB: 
			    print(pv)
        #pv_file_info[pv+'(file_names)'] = file_names

        pvs_file_info.append(pv_file_info)

    return pvs_file_info
            

