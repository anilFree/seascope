# Installation on Windows #

## Install Python and PyQt ##
  * Install python 2.x - http://www.python.org/download/
  * Install PyQt suitable for python version that you installed - http://www.riverbankcomputing.co.uk/software/pyqt/download. PyQt will install itself into python specific directory.

## Install atleast one backend ##
### For idutils backend ###
#### Install ctags, idutils ####
  * Install ctags as explained above
  * Install [GNU idutils for windows](http://gnuwin32.sourceforge.net/packages/id-utils.htm)
  * Setup PATH

### For cscope backend ###
#### Install ctags, cscope, sort ####
  * Download the windows executables from
    * seascope packaged versions at [ct\_cs\_sort\_win.zip](http://code.google.com/p/seascope/downloads/detail?name=ct_cs_sort_win.zip)
> > OR
    * latest versions at [cscope-for-windows](http://code.google.com/p/cscope-win32/), [ctags-for-windows](http://ctags.sourceforge.net/)

  * Setup path
    * PATH setting: Computer => Properties => Advanced => Environment Variables
> > OR
    * PATH setting in terminal: set PATH=c:\ct\_cs\_sort\_win\;%PATH%
> > OR
    * Copy executables to standard directory like c:\windows

  * Override system default sort.exe
> > Make sure that sort.exe overrides system default c:\windows\system32\sort.exe. Without this inverted index (-q) option of cscope won't work. More details [here](http://code.google.com/p/cscope-win32/wiki/UsageNotes)

### For gtags backend ###
#### Install ctags, GNU global/gtags ####
  * Install ctags as explained above
  * Install [GNU global for windows](http://www.gnu.org/s/global/download.html)
  * Setup PATH

## Install dot (for class graph support) ##
Install [dot/graphviz](http://www.graphviz.org/Download_windows.php)

## Running ##
Click and execute seascope/src/Seascope.py

## Screenshot ##
[screenshot-on-windows](http://qt-apps.org/CONTENT/content-pre3/135554-3.png)