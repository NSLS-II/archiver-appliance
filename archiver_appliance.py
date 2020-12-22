# -*- coding: utf-8 -*-
'''
The purpose of this module is to provide a higher level of functions, by utilizing 
the class methods implemented in epicsarchiver.py, to more easily manipulate AA

Basic Usage::
    >>> import archiver_appliance as aa
    >>> import datetime
    >>> archappl = ArchiverAppliance('archiver-01.tn.esss.lu.se')
    >>> print(archappl.version)
    >>> archappl.get_pv_status(pv='BPM*')
    >>> _end = datetime.utcnow()
    >>> df = archappl.get_data('my:pv', start='2018-07-04 13:00', end=_end)
        
'''

from __future__ import print_function
import os
import sys
from datetime import datetime
import time
import traceback
import re
import glob
from collections import OrderedDict as odict

from epicsarchiver import ArchiverAppliance

# get the Archiver's FULL hostname: localhost or hostname defined in aa.conf 
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


def _log(results, file_prefix, one_line_per_pvinfo=True):
    '''save results, which may include pv names as well as other information, 
    to a text file. one_line_per_pvinfo makes .txt file more easier to be 
    analyzied by other software such as Microsoft Excel 
    '''
    timestamp = time.strftime("-%Y%b%d_%H%M%S")
    home_dir = os.path.expanduser("~")
    _file_prefix = str(file_prefix).replace(" ", "-")
    file_name = home_dir + "/" + _file_prefix + str(timestamp)+".txt"
    
    with open(str(file_name), 'w') as fd:
        if isinstance(results[0], unicode):#string
            for result in results:
                fd.write(str(result) + "\n")
        elif isinstance(results[0], odict) or isinstance(results[0], dict):
            for pv_dict in results:
                for (k, v) in pv_dict.iteritems():
                    fd.write(str(k+"\t")+str(v)+"\t")
                    if not one_line_per_pvinfo:
                        fd.write("\n")
                fd.write("\n")

    print("{} PVs have been written to the file {}\n".format(len(results), file_name))


def _get_pvnames(results, sort=True):
    '''get PV names only, no other information'''
    if not results:
        print("No PVs found\n")
        return

    pvnames=results
    if isinstance(results[0], dict): 
        pvnames = [dic['pvName'] for dic in results]
    if sort:
        pvnames.sort()

    if len(pvnames) > 10:
        pvs_4print=pvnames[:9]
    else:
        pvs_4print=pvnames
    for pv in pvs_4print:
        print(pv)
    print("...\n%d PVs\n"%len(pvnames))

    return pvnames


def get_pvnames_from_file(filename):
    '''pvnames in 'filename' should be listed as one column'''
    with open(filename, "r") as fd:
        lines = fd.readlines()
        pvnameList = []
        for line in lines:
            if line.startswith("#") or line == "":
            # Remove empty lines and lines that start with "#"
                continue
            pvnameList.append(str(line).strip())
            
    pvnames = set(pvnameList) # remove duplicated PVs
    print("get %d PVs from %s"%(len(pvs), filename))
    return list(pvnames)


def report_pvnames(pattern='*', regex='*', limit=500, return_pvnames=False):
    '''Get pv names (up to the max. number 'limit') by 'pattern' and 'regex', then 
    write them to a file. If return_pvnames is True, then report & return pvnames
    '''
    pvs = archiver.get_all_pvs(pv=pattern, regex=regex, limit=limit)
    
    if pattern == "*":
        file_prefix = "all pvnames"
    else:
        file_prefix = str(pattern) + "-" + str(limit) + '-pvnames' 
    _log(pvs, file_prefix)
    
    if return_pvnames:
        return _get_pvnamess(pvs)
    else:
        _get_pvnames(pvs) # just report pvnames    


def report_all_pvnames():
    '''Get all pv names in the Archiver and write them to a file'''
    report_pvnames(pattern="*", regex="*", limit=-1, return_pvnames=False)


def report_waveform_pvs(log_file_info=True, return_pvnames=False):
    ''' Get a list of dicts of waveform PVs that are currently being archived,
    then try to log .pb file information (name, size) and pv names  
    '''
    results = archiver.get_archived_waveforms()
    pvnames = _get_pvnames(results)
    _log(pvnames, "all waveform pvnames");

    if log_file_info:
        pvnames = [dic['pvName'] for dic in results]
        pvnames.sort()
        info = get_pvs_file_info(pvnames)
        _log(info, "waveform file info")

    if return_pvnames:
        return pvnames


def report_storage_rate(limit=1000, return_pvnames=False):
    '''Get a list of dicts of PVs sorted by descending storage rate.
    '''
    results = archiver.get_storage_rate_report(limit=limit) 
    _log(results, "storage rate");

    if return_pvnames:
        return _get_pvnames(results, sort=False) # DO NOT sort 
    else:
        _get_pvnames(results, sort=False)


def get_pvs_file_info(pvnames, report_zero_size=True, only_report_total_size=True,
    only_report_current_year_file=True, lts_path='/DATA/lts/ArchiverStore/'):
    '''- Get archived data file name and file size for each pvname in pvnames
    pv = "SR-RF{CFD:2-Cav}E:I"; relative_path = 'SR/RF/CFD/2/Cav/E/I'
    pb_file: /DATA/lts/ArchiverStore/SR/RF/CFD/2/Cav/E/I:2016.pb
    '''
    year=time.strftime("%Y")
    pvs_file_info = []
    for pvname in pvnames:
        pv_file_info = odict()
        total_GB = 0.0
        file_names = ""
        relative_path = re.sub('[:{}-]', '/', pvname)
        full_path = lts_path + str(relative_path)
        
        for pb_file in glob.glob(full_path+'*'):
            year = "".join("".join(pb_file.rsplit(full_path+':'))).rsplit('.pb')[0]
            size_GB = round(1.0*os.path.getsize(pb_file)/(1024**3))
            total_GB += size_GB
            if not only_report_total_size:
                pv_file_info[pvname+'\t'+year] = size_GB # GB per year
            if only_report_current_year_file:
                if year == time.strftime("%Y"):
                    file_names = pb_file
                    pv_file_info[pvname+" "+year] = size_GB
            else:
                file_names += (pb_file + "    ")

        if report_zero_size:
            if not total_GB: 
                print("%s\t has no .pb files"%pvname)
                
        pv_file_info[pvname] = total_GB # total file size (GB) for  pv 
        pv_file_info[pvname+'(path)'] = full_path
        pv_file_info[pvname+'(file_names)'] = file_names

        pvs_file_info.append(pv_file_info)

    return pvs_file_info
            

