# -*- coding: utf-8 -*-
"""
@yhu: adapted from https://gitlab.esss.lu.se/ics-infrastructure/py-epicsarchiver 
@Original author: Benjamin Bertrand

The main purpose of this module is to provide BPLs as described in:
https://slacmshankar.github.io/epicsarchiver_docs/api/mgmt_scriptables.html

Documentation on all methods in the class ArchiverAppliance:  
http://slacmshankar.github.io/epicsarchiver_docs/api/org/epics/archiverappliance/
mgmt/bpl/package-summary.html

Packages required: python-requests, python-pandas, 
"""

import sys
try:
    import urllib.parse as urlparse #py3
except ImportError:
    import urlparse #py2
import requests
import pandas as pd
from datetime import datetime
import utils

# the following three libraries can be used to solve
## "HTTPError: 403 Client Error" on Debian 7 / Python 2.7.3 / requests 0.12.1  
import urllib
import urllib2
import json

import socket
localhost = socket.getfqdn() # it seems full hostname is required for AA

class ArchiverAppliance:
    """EPICS Arcvhier Appliance (AA) client

    Hold a session to the Archiver Appliance web application.

    :param hostname: EPICS Archiver Appliance hostname [default: localhost]
    :param port: EPICS Archiver Appliance management port [default: 17665]

    Basic Usage::

        >>> from epicsarchiver import ArchiverAppliance
        >>> import datetime
        >>> archappl = ArchiverAppliance('archiver-01.tn.esss.lu.se')
        >>> print(archappl.version)
        >>> archappl.get_pv_status(pv='BPM*')
        >>> _end = datetime.utcnow()
        >>> df = archappl.get_data('my:pv', start='2018-07-04 13:00', end=_end)
    """

    def __init__(self, hostname=localhost, port=17665):
        self.hostname = hostname
        #self.mgmt_url = f"http://{hostname}:{port}/mgmt/bpl/"  # py3
        self.mgmt_url = "http://{}:{}/mgmt/bpl/".format(hostname, port) #py2
        self._info = None
        self._data_url = None
        self.session = requests.Session()
        #self.session.auth = ('user', 'pass')
 
    def _return_json(self, r):
        try:
            return r.json() # for > python-2.7.3
        except:
            return r.json   # for Debian 7.11: python-2.7.3, requests-0.12.1

    def request(self, method, *args, **kwargs):
        r"""Sends a request using the session

        :param method: HTTP method
        :param \*args: Optional arguments
        :param \*\*kwargs: Optional keyword arguments
        :return: :class:`requests.Response <Response>` object
        """
        #headers = {'content-type': 'application/json'}
        r = self.session.request(method, *args, **kwargs)
        r.raise_for_status()
        return r

    def get(self, endpoint, **kwargs):
        r"""Send a GET request to the given endpoint

        :param endpoint: API endpoint (relative or absolute)
        :param \*\*kwargs: Optional arguments to be sent
        :return: :class:`requests.Response <Response>` object
        """
        #url = urllib.parse.urljoin(self.mgmt_url, endpoint.lstrip("/"))
        url = urlparse.urljoin(self.mgmt_url, endpoint.lstrip("/"))
        return self.request("GET", url, **kwargs)

    def post(self, endpoint, **kwargs):
        r"""Send a POST request to the given endpoint

        :param endpoint: API endpoint (relative or absolute)
        :param \*\*kwargs: Optional arguments to be sent
        :return: :class:`requests.Response <Response>` object
        """
        url = urlparse.urljoin(self.mgmt_url, endpoint.lstrip("/"))
        return self.request("POST", url, **kwargs)

    @property
    def info(self):
        """EPICS Archiver Appliance information"""
        if self._info is None:            
            r = self.get("/getApplianceInfo")
            self._info = self._return_json(r)
        return self._info

    @property
    def identity(self):
        """EPICS Archiver Appliance identity"""
        return self.info.get("identity")

    @property
    def version(self):
        """EPICS Archiver Appliance version"""
        return self.info.get("version")

    @property
    def data_url(self):
        """EPICS Archiver Appliance data retrieval url"""
        if self._data_url is None:
            self._data_url = self.info.get("dataRetrievalURL") + "/data/getData.json"
        return self._data_url

    def get_all_expanded_pvs(self):
        """Return all expanded PV names in the cluster. 
        (yhu-2020-Dec-22: it seems this method does not work)

        This is targeted at automation and should return the PVs
        being archived, the fields, .VAL's, aliases and PV's in
        the archive workflow.
        Note this call can return 10's of millions of names.

        :return: list of expanded PV names
        """
        try:
            r = self.get("/getAllExpandedPVNames")
            return self._return_json(r)
        except:
            url = self.mgmt_url + 'getAllExpandedPVNames'
            return(self.request_by_urllib2(url))

    def get_all_pvs(self, pv=None, regex=None, limit=500):
        """Return all the PVs in the cluster

        :param pv: An optional argument that can contain a GLOB wildcard.
                   Will return PVs that match this GLOB.
                   For example: pv=KLYS*
        :param regex: An optional argument that can contain a Java regex \
                      wildcard.
                      Will return PVs that match this regex.
        :param limit: number of matched PV's that are returned.
                      To get all the PV names, (potentially in the millions),
                      set limit to –1. Default to 500.
        :return: list of PV names
        """
        params = {"limit": limit}
        if pv is not None:
            params["pv"] = pv
        if regex is not None:
            params["regex"] = regex
        r = self.get("/getAllPVs", params=params)
        return self._return_json(r)

    def get_pv_status(self, pv):
        """Return the status of a PV

        :param pv: name(s) of the pv for which the status is to be determined.
                   Can be a GLOB wildcards or multiple PVs as a comma separated list.
        :return: list of dict with the status of the matching PVs
        """
        r = self.get("/getPVStatus", params={"pv": pv})
        return self._return_json(r)

    def get_pv_status_from_files(self, files, appliance=None):
        """Return the status of PVs from a list of files

        :param files: list of files in CSV format with PVs to archive.
        :param appliance: optional appliance to use to archive PVs (in a cluster)
        :return: list of dict with the status of the matching PVs
        """
        pvs = utils.get_pvs_from_files(files, appliance)
        pvs = ",".join(map(lambda pv: pv["pv"], pvs))
        return self.get_pv_status(pvs)

    def get_unarchived_pvs(self, pvs):
        """Return the list of unarchived PVs out of PVs specified in pvs
        (yhu-2020-Dec-22: it seems this method does not work)

        :param pvs: a list of PVs either in CSV format or as a python string list
        :return: list of unarchived PV names
        """
        if isinstance(pvs, list):
            pvs = ",".join(pvs)
        r = self.post("/unarchivedPVs", data={"pv": pvs})
        return self._return_json(r)

    def get_unarchived_pvs_from_files(self, files, appliance=None):
        """Return the list of unarchived PVs from a list of files

        :param files: list of files in CSV format with PVs to archive.
        :param appliance: optional appliance to use to archive PVs (in a cluster)
        :return: list of unarchived PV names
        """
        pvs = utils.get_pvs_from_files(files, appliance)
        pvs = ",".join(map(lambda pv: pv["pv"], pvs))
        return self.get_unarchived_pvs(pvs)

    def archive_pv(self, pv, **kwargs):
        r"""Archive a PV

        :param pv: name of the pv to be achived.
                   Can be a comma separated list of names.
        :param \*\*kwargs: optional extra keyword arguments
            - samplingperiod
            - samplingmethod
            - controllingPV
            - policy
            - appliance
        :return: list of submitted PVs
        """
        params = {"pv": pv}
        params.update(kwargs)
        try:
            r = self.get("/archivePV", params=params)
            return self._return_json(r)
        except:
            pvname = urllib.urlencode({'pv' : pv})
            url = self.mgmt_url + 'archivePV?' + pvname
            return(self.request_by_urllib2(url))
            
    def archive_pvs(self, pvs):
        """Archive a list of PVs

        :param pvs: list of PVs (as dict) to archive
        :return: list of submitted PVs
        """
        r = self.post("/archivePV", json=pvs)
        return self._return_json(r)

    def archive_pvs_from_files(self, files, appliance=None):
        """Archive PVs from a list of files

        :param files: list of files in CSV format with PVs to archive.
        :param appliance: optional appliance to use to archive PVs (in a cluster)
        :return: list of submitted PVs
        """
        pvs = utils.get_pvs_from_files(files, appliance)
        return self.archive_pvs(pvs)

    def _get_or_post(self, endpoint, pv):
        """Send a GET or POST if pv is a comma separated list

        :param endpoint: API endpoint
        :param pv: name of the pv.
                   Can be a GLOB wildcards or a list of comma separated names.
        :return: list of submitted PVs
        """
        if "," in pv:
            r = self.post(endpoint, data=pv)
        else:
            r = self.get(endpoint, params={"pv": pv})
        return self._return_json(r)

    def request_by_urllib2(self, url):
        """Another way to make a request to the Archiver server. It solves the
        problem "HTTPError: 403 Client Error"
        """
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        the_page = response.read()
        return json.loads(the_page)

    def pause_pv(self, pv):
        """Pause the archiving of a PV(s)

        :param pv: name of the pv.
                   Can be a GLOB wildcards or a list of comma separated names.
        :return: list of submitted PVs
        """
        try:
            # on Debian 7: HTTPError: 403 Client Error
            return self._get_or_post("/pauseArchivingPV", pv) 
        except:
            # on Debian 7: the following works
            pvname = urllib.urlencode({'pv' : pv})
            url = self.mgmt_url + 'pauseArchivingPV?' + pvname
            return(self.request_by_urllib2(url))

    def resume_pv(self, pv):
        """Resume the archiving of a PV(s)

        :param pv: name of the pv.
                   Can be a GLOB wildcards or a list of comma separated names.
        :return: list of submitted PVs
        """
        try:
            return self._get_or_post("/resumeArchivingPV", pv)
        except:
            pvname = urllib.urlencode({'pv' : pv})
            url = self.mgmt_url + 'resumeArchivingPV?' + pvname
            return(self.request_by_urllib2(url))

    def abort_pv(self, pv):
        """Abort any pending requests for archiving this PV.

        :param pv: name of the pv.
        :return: list of submitted PVs
        """
        try:
            r = self.get("/abortArchivingPV", params={"pv": pv})
            return self._return_json(r)
        except:
            pvname = urllib.urlencode({'pv' : pv})
            url = self.mgmt_url + 'abortArchivingPV?' + pvname
            return(self.request_by_urllib2(url))            

    def delete_pv(self, pv, delete_data=False):
        """Stop archiving the specified PV.

        The PV needs to be paused first.

        :param pv: name of the pv.
        :param delete_data: delete the data that has already been recorded.
                            Default to False.
        :return: list of submitted PVs
        """
        try:
            r = self.get("/deletePV", params={"pv": pv, "delete_data": delete_data})
            return self._return_json(r)
        except:
            if delete_data:
                url = self.mgmt_url + '/deletePV?pv=' + urllib.quote_plus(pv) + \
                      "&deleteData=true"
            else:
                url = self.mgmt_url + '/deletePV?pv=' + urllib.quote_plus(pv) + \
                      "&deleteData=False"
            return self.request_by_urllib2(url)

    def rename_pv(self, pv, newname):
        """Rename this pv to a new name.

        The PV needs to be paused first.

        :param pv: name of the pv.
        :param newname: new name of the pv
        :return: list of submitted PVs
        """
        r = self.get("/renamePV", params={"pv": pv, "newname": newname})
        return self._return_json(r)

    def update_pv(self, pv, new_period=1.0, sampling_method='MONITOR', **kargs):
        """Change the archival parameters for a PV

        :param pv: name of the pv.
        :param new_period: the new sampling period in seconds.
        :param sampling_method: the new sampling method [SCAN|MONITOR]
        :return: list of submitted PV
        """
        params = {"pv": pv, "samplingperiod": new_period}
        if sampling_method:
            params["samplingmethod"] = sampling_method
        try:
            r = self.get("/changeArchivalParameters", params=params)
            return self._return_json(r)
        except:            
            url = self.mgmt_url + 'changeArchivalParameters?pv=' + \
            urllib.quote_plus(pv)+'&'+urllib.urlencode({"samplingperiod":new_period,\
            "samplingmethod": sampling_method})
            return self.request_by_urllib2(url)

    def get_data(self, pv, start, end):
        """Retrieve archived data

        :param pv: name of the pv.
        :param start: start time. Can be a string or `datetime.datetime` object.
        :param end: end time. Can be a string or `datetime.datetime` object.
        :return: `pandas.DataFrame`
        """
        # http://slacmshankar.github.io/epicsarchiver_docs/userguide.html
        params = {
            "pv": pv,
            "from": utils.format_date(start),
            "to": utils.format_date(end),
        }
        try:
            r = self.get(self.data_url, params=params)
            data = self._return_json(r)
        except:
            url = self.data_url + "?pv=" + urllib.quote_plus(pv) + '&' + \
urllib.urlencode({"from":utils.format_date(start), "to":utils.format_date(end)})
            print(url)
            req = urllib2.urlopen(url)
            data = json.load(req)
            #data = self.request_by_urllib2(url)
        df = pd.DataFrame(data[0]["data"])
        #print(df)
        try:
            if pd.__version__ > '0.8.0':
                df["date"] = pd.to_datetime(df["secs"] + df["nanos"] * 1e-9, unit="s")
            else:
                df["date"] = pd.to_datetime([datetime.fromtimestamp(x["secs"] + \
                                x["nanos"] * 1e-9,) for x in data[0]["data"]])
        except KeyError:
            # Empty data
            pass
        else:
            df = df[["date", "val"]]
            df = df.set_index("date")
        return df

    def pause_rename_resume_pv(self, pv, new, debug=False):
        """Pause, rename and resume a PV

        :param pv: name of the pv
        :param new: new name of the pv
        :param bool debug: enable debug logging
        :return: None
        """
        result = self.get_pv_status(pv)
        if result[0]["status"] != "Being archived":
            sys.stderr.write("PV {} isn't being archived. Skipping.\n".format(pv))
            return
        result = self.get_pv_status(new)
        if result[0]["status"] != "Not being archived":
            sys.stderr.write("New PV {} already exists. Skipping.\n".format(new))
            return
        result = self.pause_pv(pv)
        if not utils.check_result(result, "Error while pausing {}".format(pv)):
            return
        result = self.rename_pv(pv, new)
        if not utils.check_result(result,"Error: renaming {} to {}").format(pv,new):
            return
        result = self.resume_pv(new)
        if not utils.check_result(result, "Error while resuming {}".format(new)):
            return
        if debug:
            print("PV {} successfully renamed to {}".format(pv, new))

    def rename_pvs_from_files(self, files, debug=False):
        """Rename PVs from a list of files

        Each PV will be paused, renamed and resumed

        :param files: list of files in CSV format with PVs to rename.
        :return: None
        """
        pvs = utils.get_rename_pvs_from_files(files)
        for (current, new) in pvs:
            self.pause_rename_resume_pv(current, new, debug)
    
    def get_pv_type_info(self, pv):
        """Get the type info for a given PV. In the AA terminology, 
        the PVTypeInfo contains the various archiving parameters for a PV.

        :param pv: The name of the pv.
        :return: a dict with details (hostname, RTYP, ...) about the PV
        """
        r = self.get("/getPVTypeInfo", params={"pv": pv})
        return self._return_json(r)

    def get_never_connected_pvs(self):
        """Get a list of PVs that have never connected. This corresponds to 
        the report of "PV's that may not exist" on the web interface

        :return: a list of dicts including keys of pvName, requestTime, etc.  
        """
        r = self.get("/getNeverConnectedPVs")
        return self._return_json(r)

    def get_currently_disconnected_pvs(self):
        """Get a list of PVs that are currently disconnected.

        :return: a list of dicts including keys of pvName, lastKnownEvent, etc.  
        """
        r = self.get("/getCurrentlyDisconnectedPVs")
        return self._return_json(r)

    def get_event_rate_report(self, limit=1000):
        """Return a list of dicts of PVs sorted by descending event rate.

        :param limit: Limit this report to 'limit' PVs per appliance in the cluster.
        :return: a list of dicts with keys of pvName and eventRate.
        """
        r = self.get("/getEventRateReport", params={"limit": limit})  
        return self._return_json(r)

    def get_storage_rate_report(self, limit=1000):
        """Return a list of dicts of PVs sorted by descending storage rate.

        :param limit: Limit this report to 'limit' PVs per appliance in the cluster.
        :return: a list of dicts with keys of pvName, storageRate_GBperYear, etc.
        """
        r = self.get("/getStorageRateReport", params={"limit": limit})  
        return self._return_json(r)

    def get_storage_consumed_report(self, limit=1000):
        """Return a list of dicts of PVs sorted by descending storage consumed.

        :param limit: Limit this report to 'limit' PVs per appliance in the cluster.
        :return: a list of dicts with keys of pvName, storageConsumedInMB, etc.
        """
        r = self.get("/getPVsByStorageConsumed", params={"limit": limit})  
        return self._return_json(r)
        
    def get_paused_pvs_report(self, limit=None):
        """Return a list of PVs that are currently paused.

        :param limit: Optional. Limit this report to 'limit' PVs per appliance.
        :return: a list of dicts with keys of pvName, modificationTime, etc.
        """
        r = self.get("/getPausedPVsReport", )  
        return self._return_json(r)

    def get_archived_waveforms(self):
        """Get a list of waveform PVs that are currently being archived.

        :return: a list of dicts including keys of pvName, elementCount, etc.  
        """
        r = self.get("/getArchivedWaveforms")
        return self._return_json(r)

    def get_overflow_report(self, limit=1000):
        """Get a list of PVs that are dropping events because of buffer overflow.

        :return: a list of dicts including keys of pvName, elementCount, etc.  
        """
        r = self.get("/getPVsByDroppedEventsBuffer", params={"limit": limit})
        return self._return_json(r)
