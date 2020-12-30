This package provides a bunch of python functions to manage Archiver Appliance.

==Quick Start==

Open a terminal, git clone this repository, type "cd pyAA", then type "ipython" 
or "python", or other python shells: 

    >>> import aa
    
    >>> aa.report_currently_disconnected_pvs()
    
    >>> aa.report_never_connected_pvs()
    
    >>> aa.report_paused_pvs()
    
    >>> aa.abort_pvs()
    
    >>> aa.pause_pvs()
    
    >>> aa.delete_pvs_and_data()


==More info==

Basically, just as a common practice, after you do "import aa", you should type 
"aa.", then use the Tab key to see a list of aa.* if you use ipython. If you use
the basic python shell which does not support the Tab key, then type "help(aa)".
Always remember to type "help(aa.function_name)", i.e. help(aa.delete_pvs_and_data)
if you look for advanced usages of a function provided by this package.

Here is the list of functions you could use with various keyword arguments.

