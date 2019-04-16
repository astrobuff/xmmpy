#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 13 15:00:00 2019

Using the perCCD spectral files for a set of observations
perform a fit to the Cu Kalpha line (8.04 keV)

Using the spectra from the testing long-term CTI CCF and only double events 

save the results and the plots

@author: ivaltchanov
"""

# In[1]:

import os
import sys
import numpy as np
#import threading
from datetime import datetime

from astropy.io import fits
from astropy.table import Table
from astropy.convolution import convolve, Box1DKernel

import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pylab as plt

import seaborn as sns
sns.set(style="white")

plt.rc('text', usetex=False)
plt.rc('font', family='serif')

home = os.path.expanduser('~')
sys.path.append(home + '/IVAN/python')

from xmm_tools import read_pn_obstable, fit_cu_line, run_command
#%%
# loop over all OBS_IDs
#
outputDir = home + '/IVAN/Cu-line'
plotDir = home + '/IVAN/Cu-line/plots'
#
t = Table.read(f"{outputDir}/fit_results_cuka.csv")
obslist = np.unique(t['obsid'])
#obslist = [804680101]
nw = len(obslist)
#
# relative times
time0 = datetime.strptime("2000-01-01T00:00:00","%Y-%m-%dT%H:%M:%S")
#
# file for output
#
fout = open(f"{outputDir}/fit_results_cuka_doubles_cti48.csv","w")
#
print ("obsid,rev,delta_time,ontime,ccd,lineE,lineE_err,fwhm,fwhm_err,chi2,df",file=fout)
#
for ik,iobs in enumerate(obslist):
    obsid = f"{iobs:010}"
    print (f"Doing OBS_ID: {obsid} ({ik+1}/{nw})")
    # Now fit
    smooth = 7
    fig, axs = plt.subplots(2,6,sharex=True,sharey=True,figsize=(15,10))
    for j in range(12):
        ccd = f"{j+1:02}"
        #slices = glob.glob(f"{specDir}/pn_{ccd:02}_180_spec5.fits")
        slices = f"{outputDir}/{obsid}/PN_LW/pn_{ccd}_doubles_spec5.fits"
        if (not os.path.isfile(slices)):
            raise FileNotFoundError
        #
        hdu = fits.open(slices)
        #
        rev = hdu[0].header["REVOLUT"]
        start_time = hdu[0].header['DATE-OBS']
        stime = datetime.strptime(start_time,"%Y-%m-%dT%H:%M:%S")
        delta_time = (stime-time0).total_seconds()/(365.0*24.0*3600.0) # in years
        #
        spec = hdu['SPECTRUM']
        ontime = spec.header["EXPOSURE"]
        channel = spec.data['CHANNEL']*5.0/1000.0
        counts = spec.data['COUNTS']
        y = convolve(counts, Box1DKernel(smooth))
        # now fit a simple linear + Gauss line model
        #
        (fit_out,fit_res) = fit_cu_line(channel,counts,line_c=8.04)
        fitted_peak = fit_out.params['g1_height'].value
        if (fitted_peak > 90.0):
            ymax = 150.0
        else:
            ymax = 100.0
        #print (f"Fitted height for CCD {ccd}: {fitted_peak}")
        output = f"{obsid},{rev},{delta_time:.4f},{ontime:.2f},{ccd},{fit_res}"
        print (output,file=fout)
        #
        yfitted = fit_out.eval(x=channel)
        #print (f"Fitting CCD #{ccd:02}",fit_res)
        k = j
        kj = 0
        if (j >= 6):
            k = j - 6
            kj = 1
        if (ccd == "03"):
            axs[kj,k].set_title(f"OBS_ID: {rev}_{obsid}")
        if (ccd == "09"):
            axs[kj,k].set_xlabel("Energy (keV)")
        if (ccd == "07"):
            axs[kj,k].set_ylabel("Counts")
        axs[kj,k].plot(channel,counts,label=f'CCD #{ccd}')
        axs[kj,k].plot(channel,y,label='')
        axs[kj,k].plot(channel,yfitted,color='red',label='')
        axs[kj,k].axvline(8.04, color='lime',ls='dashed',linewidth=2)
        axs[kj,k].set_xlim((7,9))
        axs[kj,k].set_ylim((0,ymax))
        axs[kj,k].grid(True)
        axs[kj,k].legend()
        #axs[kj,k].set_title(f"CCD #{ccd}")
    #
    plt.subplots_adjust(wspace=0, hspace=0)
    #plt.text(-13,-1,'Energy (keV)',ha='center', va='center')
    #plt.text(-36,10,'Counts',rotation='vertical',ha='center', va='center')
    #plt.tight_layout()
    plt.savefig(f"{plotDir}/{obsid}_CuKa_doubles_cti48_plot.png",dpi=100)
    #plt.show()
    plt.close()
#
fout.close()
print ("All done")