# -*- coding: utf-8 -*-
"""Main module."""
import sys
try:
    import urllib.parse as urlparse #py3
except ImportError:
    import urlparse #py2
import requests
import pandas as pd
#from . import utils
import utils
import urllib
import urllib2
import json

class ArchiverAppliance:
    """EPICS Arcvhier Appliance client

    Hold a session to the Archiver Appliance web application.

    :param hostname: EPICS Archiver Appliance hostname [default: localhost]
    :param port: EPICS Archiver Appliance management port [default: 17665]

    Basic Usage::

        >>> from epicsarchiver import ArchiverAppliance
        >>> archappl = ArchiverAppliance('archiver-01.tn.esss.lu.se')
        >>> print(archappl.version)
        >>> archappl.get_pv_status(pv='BPM*')
        >>> df = archappl.get_data('my:pv', start='2018-07-04 13:00', end=datetime.utcnow())
    """

    def __init__(self, hostname="localhost", port=17665):
        self.hostname = hostname
        #self.mgmt_url = f"http://{hostname}:{port}/mgmt/bpl/"  # py3
        self.mgmt_url = "http://{}:{}/mgmt/bpl/".format(hostname, port) #py2
        self._info = None
        self._data_url = None
        self.session = requests.Session()
        #self.session.auth = ('user', 'pass')

    def request(self, method, *args, **kwargs):
        r"""Sends a request using the session

        :param method: HTTP method
        :param \*args: Optional arguments
        :param \*\*kwargs: Optional keyword arguments
        :return: :class:`requests.Response <Response>` object
        """
        headers = {'content-type': 'application/json'}
        r = self.session.request(method, *args, headers=headers, **kwargs)
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
        #print(url)
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
            # http://slacmshankar.github.io/epicsarchiver_docs/api/org/epics/archiverappliance/mgmt/bpl/GetApplianceInfo.html
            r = self.get("/getApplianceInfo")
            try:
                self._info = r.json() # > python-2.7.3  
            except:
                self._info = r.json  # <= python-2.7.3 & requests-0.12.1 (Debian 7)
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

        This is targeted at automation and should return the PVs
        being archived, the fields, .VAL's, aliases and PV's in
        the archive workflow.
        Note this call can return 10's of millions of names.

        :return: list of expanded PV names
        """
        # http://slacmshankar.github.io/epicsarchiver_docs/api/org/epics/archiverappliance/mgmt/bpl/GetAllExpandedPVNames.html
        r = self.get("/getAllExpandedPVNames")
        try:
            return r.json()
        except:
            return r.json

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
        # http://slacmshankar.github.io/epicsarchiver_docs/api/org/epics/archiverappliance/mgmt/bpl/GetAllPVs.html
        params = {"limit": limit}
        if pv is not None:
            params["pv"] = pv
        if regex is not None:
            params["regex"] = regex
        r = self.get("/getAllPVs", params=params)
        try:
            return r.json()
        except:
            return r.json

    def get_pv_status(self, pv):
        """Return the status of a PV

        :param pv: name(s) of the pv for which the status is to be determined.
                   Can be a GLOB wildcards or multiple PVs as a comma separated list.
        :return: list of dict with the status of the matching PVs
        """
        # http://slacmshankar.github.io/epicsarchiver_docs/api/org/epics/archiverappliance/mgmt/bpl/GetPVStatusAction.html
        r = self.get("/getPVStatus", params={"pv": pv})
        try:
            return r.json()
        except:
            return r.json

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

        :param pvs: a list of PVs either in CSV format or as a python string list
        :return: list of unarchived PV names
        """
        # https://slacmshankar.github.io/epicsarchiver_docs/api/org/epics/archiverappliance/mgmt/bpl/UnarchivedPVsAction.html
        if isinstance(pvs, list):
            pvs = ",".join(pvs)
        r = self.post("/unarchivedPVs", data={"pv": pvs})
        try:
            return r.json()
        except:
            return r.json

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
        # http://slacmshankar.github.io/epicsarchiver_docs/api/org/epics/archiverappliance/mgmt/bpl/ArchivePVAction.html
        params = {"pv": pv}
        params.update(kwargs)
        print(params)
        r = self.get("/archivePV", params=params)
        try:
            return r.json()
        except:
            return r.json

    def archive_pvs(self, pvs):
        """Archive a list of PVs

        :param pvs: list of PVs (as dict) to archive
        :return: list of submitted PVs
        """
        # http://slacmshankar.github.io/epicsarchiver_docs/api/org/epics/archiverappliance/mgmt/bpl/ArchivePVAction.html
        r = self.post("/archivePV", json=pvs)
        try:
            return r.json()
        except:
            return r.json

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
        try:
            return r.json()
        except:
            return r.json

    def pause_pv(self, pv):
        """Pause the archiving of a PV(s)

        :param pv: name of the pv.
                   Can be a GLOB wildcards or a list of comma separated names.
        :return: list of submitted PVs
        """
        # http://slacmshankar.github.io/epicsarchiver_docs/api/org/epics/archiverappliance/mgmt/bpl/PauseArchivingPV.html
        #try:
        return self._get_or_post("/pauseArchivingPV", pv) #HTTPError: 403 Client Error
        #except:
        #    pvname = urllib.urlencode({'pv' : pv})
        #    url = self.mgmt_url + 'pauseArchivingPV?' + pvname
        #    print("Pausing request for pv %s using url %s"%(pv, url))
        #    req = urllib2.Request(url)
        #    response = urllib2.urlopen(req)
        #    the_page = response.read()
        #    pauseResponse = json.loads(the_page)
        #    return pauseResponse

    def resume_pv(self, pv):
        """Resume the archiving of a PV(s)

        :param pv: name of the pv.
                   Can be a GLOB wildcards or a list of comma separated names.
        :return: list of submitted PVs
        """
        # http://slacmshankar.github.io/epicsarchiver_docs/api/org/epics/archiverappliance/mgmt/bpl/ResumeArchivingPV.html
        return self._get_or_post("/resumeArchivingPV", pv)

    def abort_pv(self, pv):
        """Abort any pending requests for archiving this PV.

        :param pv: name of the pv.
        :return: list of submitted PVs
        """
        # http://slacmshankar.github.io/epicsarchiver_docs/api/org/epics/archiverappliance/mgmt/bpl/AbortArchiveRequest.html
        r = self.get("/abortArchivingPV", params={"pv": pv})
        try:
            return r.json()
        except:
            return r.json

    def delete_pv(self, pv, delete_data=False):
        """Stop archiving the specified PV.

        The PV needs to be paused first.

        :param pv: name of the pv.
        :param delete_data: delete the data that has already been recorded.
                            Default to False.
        :return: list of submitted PVs
        """
        # http://slacmshankar.github.io/epicsarchiver_docs/api/org/epics/archiverappliance/mgmt/bpl/DeletePV.html
        try:
            r = self.get("/deletePV", params={"pv": pv, "delete_data": delete_data})
            #r = self.get("/deletePV", params={"pv": pv, "deleteData": delete_data})
            try:
                return r.json()
            except:
                return r.json
        except:
            url = self.mgmt_url + '/deletePV?pv=' + urllib.quote_plus(pv) + "&deleteData=true"
            req = urllib2.Request(url)
            response = urllib2.urlopen(req)
            the_page = response.read()
            deletePVResponse = json.loads(the_page)
            return deletePVResponse


    def rename_pv(self, pv, newname):
        """Rename this pv to a new name.

        The PV needs to be paused first.

        :param pv: name of the pv.
        :param newname: new name of the pv
        :return: list of submitted PVs
        """
        # https://slacmshankar.github.io/epicsarchiver_docs/api/org/epics/archiverappliance/mgmt/bpl/RenamePVAction.html
        r = self.get("/renamePV", params={"pv": pv, "newname": newname})
        try:
            return r.json()
        except:
            return r.json

    def update_pv(self, pv, samplingperiod, samplingmethod=None):
        """Change the archival parameters for a PV

        :param pv: name of the pv.
        :param samplingperiod: the new sampling period in seconds.
        :param samplingmethod: the new sampling method [SCAN|MONITOR]
        :return: list of submitted PV
        """
        # http://slacmshankar.github.io/epicsarchiver_docs/api/org/epics/archiverappliance/mgmt/bpl/ChangeArchivalParamsAction.html
        params = {"pv": pv, "samplingperiod": samplingperiod}
        if samplingmethod:
            params["samplingmethod"] = samplingmethod
        r = self.get("/changeArchivalParameters", params=params)
        try:
            return r.json()
        except:
            return r.json

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
        r = self.get(self.data_url, params=params)
        try:
            data = r.json()
        except:
            data = r.json
        df = pd.DataFrame(data[0]["data"])
        try:
            df["date"] = pd.to_datetime(df["secs"] + df["nanos"] * 1e-9, unit="s")
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
        if not utils.check_result(result, "Error while renaming {} to {}").format(pv, new):
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
