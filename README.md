==Introduction==

This package, pyAA, provides a bunch of python functions to manage Archiver Appliance (AA).
It has been tested under both python 2 and python 3.

The Archiver itself provides an easy-to-use web interface where you can view and 
manage many things. Suppose somehow there are thousands of never connected PVs 
(PV's that may not exist). In order to add new PVs to the Archiver, you have to 
abort those never connected PVs. You could do the aborting manually through the 
web interface by lots of mouse clicks. However, you can get the aborting done in 
a few seconds if you use this package.

If you can not easily get something done through the web interface, then this 
python package is an easy-yet-powerful tool for you.      
 

==Quick Start==

Although you can use this package on any Linux computer which can talk to the Archiver
server, it is recommended that you should use this package on the Archiver server because
some functions need to access the local data files (.pb files).

Required python packages: requests, pandas. It is recommended that you should install 
these dependencies before you use pyAA.  

Open a terminal on the Achiver server, git clone this repository, then type "cd archiver-appliance".
It is recommended that you should take a look at 'pyAA/aa.conf' and make changes accordingly.
After you are done with 'aa.conf', type "ipython" or "python", or other python shells: 

    >>> from pyAA import aa
    
    >>> help(aa)
    
    >>> help(aa.report_never_connected_pvs)
    
    >>> aa.report_never_connected_pvs()
    
    >>> aa.report_currently_disconnected_pvs()
    
    >>> aa.report_paused_pvs()
    
    >>> aa.abort_pvs()
    
    >>> aa.pause_pvs()
    
    >>> aa.delete_pvs_and_data()

Basically, just as a common practice, after you do "from pyAA import aa", you should type 
"aa.", then use the Tab key to see a list of aa.* if you use ipython. If you use
the basic python shell which does not support the Tab key, then type "help(aa)".
Always remember to type "help(aa.function_name)", i.e. help(aa.delete_pvs_and_data)
if you look for advanced usages of a function provided by this package.

You can install this package to the python system path (i.e./usr/local/lib/python*/dist-packages/)
so that other people can use it. This is how to install this package locally (suppose 
you are already in the directory "archiver-appliance"):

    sudo python setup.py install
    

==More info ...==

Most functions in this package have default arguments to get default behaviors. 
You could use various keyword arguments to change the default behavior of a function.
  
    1) do_return=True: return pv names (only pv names) if set True (default is False), 
    i.e. pvnames = aa.report_never_connected_pvs(do_return=True) --> pvnames is a list of 
    never connected pv names. This argument can be used for all report_*() functions; 
    
    2) log_file_info=True: write archived data file info (file name, file size, etc.) 
    to a text file if set True. The file could be easily viewed and analyzed by 
    MS Excel or OpenOffice Spreadsheet(Insert Sheet from File ...);
        
    3) filename='/path/to/pvlist.txt': this argument can be used in 
    report_pvs_from_file() and all "action" functions including abort_pvs(), 
    pause_pvs(), delete_pvs_and_data(), etc. You should give a valid path to the file; 
    
    4) pattern=something-like-'SR:C03-BI*': mainly used for report_pvs(); 
     
    5) regex='*': mainly used for report_pvs();  
    
    6) limit=max-number-of-pvs: for report_pvs(), report_storage_rate(), etc.; 
    
    7) one_line_per_pvinfo: if False, key & value per line in the log file;
    
    8) sort: if False, pv names are not sorted.
    
    And the following can be used if log_file_info=True: 
        lts_path: this is very important, you have to set the correct "Path" in aa.conf; 
        only_report_total_size: if set False, then all *.pb file sizes are logged; 
        only_report_current_year: if set False, then all .pb file names are logged;


Below is the list of functions:

  The following 10 functions do all kind of reports, meaning they only read something from AA. 

    1. aa.report_never_connected_pvs(): as "PV's that may not exist" on the web interface.

    2. aa.report_currently_disconnected_pvs(): these pvs used to be connected.
    
    3. aa.report_paused_pvs(): these pvs could be resumed or deleted. 
    
    4. aa.report_pvs(): aa.report_pvs(pattern='SR:C03-BI*', limit=100) will report 
    up to 100 PVs starting with 'SR:C03-BI'.   

    5. aa.report_all_pvs(): you can use aa.report_all_pvs(log_file_info=True) to see
    how much data archived for each PV in all PVs.   
    
    6. aa.report_pvs_from_file(): if you just want to know the storage info of a few PVs, 
    use aa.report_pvs_from_file(filename='/home/your-account/test.txt', log_file_info=True).
    
    7. aa.report_waveform_pvs(): these pvs are array-type-record: waveform, compress, aSub, etc.
    
    8. aa.report_storage_rate(): sorted by descending storage rate.
    
    9. aa.report_storage_consumed(): sorted by descending storage consumed.
    
    10. aa.report_overflow_pvs(): 'overflow' means a PV is updating too fast that not all values
    are archived. So, you probably need to use aa.change_pvs_archival_parameters(). 
    
  The following 6 functions perform all kinds of actions, meaning they make changes on AA. 
  So, think before you act. 
        
    11. aa.abort_pvs(): by default, this function aborts all never connected pvs as
    reported by #1 aa.report_never_connected_pvs().
    
    You can use aa.abort_pvs(['pv1', 'pv2']) or aa.abort_pvs('path-to-a-file') to abort
    a list of PVs you want to abort. You can use ['pv1', 'pv2'] or 'path-to-a-file' 
    for the following 5 functions. 
    
    12. aa.pause_pvs(): by default, this function pauses all currently disconnected pvs
    as reported by #2 aa.report_currently_disconnected_pvs(). See #11 for non-default.
    
    13. aa.resume_pvs(): by default, this function resumes all currently paused 
    pvs as reported by #3 aa.report_paused_pvs(). See #11 for non-default.

    14. aa.delete_pvs_only(): by default, this function deletes all currently 
    paused pvs as reported by #3 aa.report_paused_pvs(). The PVs' data are kept. 

    15. aa.delete_pvs_and_data(): by default, this function deletes all currently 
    paused pvs as reported by #3 aa.report_paused_pvs(). The PVs' data are also 
    deleted by default. You can use two keyword arguments to delete partial archived data: 
    aa.delete_pvs_and_data(['pv1', 'pv2'], start_year=0, end_year=2017).  
    
    This function is very destructive: it deletes archived data (.pb files). Use 
    the function aa.delete_pvs_only() if the Archiver system has enough disk space 
    and you do not want to delete any data.   
    
    16. aa.change_pvs_archival_parameters(['pv1', 'pv2']): update archival parameters 
    (sampling period, sampling method) of a list of PVs. 
    
    If 'python-cothread' is installed, you can use aa.get_reconnected_pvnames() to get
    those paused pv names, which are online again.
