import xarray as xr
import numpy as np
import sys
from math import nan

def bootgen(darray, nsamples=None, seed=None, nboots=1000, resample=True):
    """Generate nboots bootstrap samples from darray with nsamples within each bootstrap.
    Sampling is done from the left most dimension
    If nsamples = None then nsamples = the length of the left most dimension.

    Input:
        darray = the data array on which you want to do the resampling (on the left most dimension)

    Optional input:
        nsamples = the number of members to go into each bootstrap samples.
        seed = an optional number to put in for the random number seed.  Required in 
               cases where reproducibility is needed.
        nboots = the number of bootstrap samples consisting of nsamples each

    """

    if (~(resample) & (nsamples == None)):
        print("You can't use nsamples == None and resample=False")
        sys.exit()
#    else:
#        dims = darray.dims
#        if (nsamples > (darray[dims[0]].size / 2.)):
#           print("Warning, you've chosen to not resample, but also have a large sample size compared to your dataset")


    def resolve_duplicates(dat):
        u, c = np.unique(dat, return_counts=True)
        if (np.max(c) > 1):
            idup = np.argwhere( c > 1 )
            for i in np.arange(0,len(idup),1):
                dupval = u[idup[i]]
                print(dupval)
                duparg = np.argwhere( dat == dupval )
                for j in np.arange(1,len(duparg),1):
                    ichange = duparg[j]
                    while True:
                        newval = np.floor(np.random.uniform(0,nmemin,1)).astype(int)
                        test = ( (dat - newval) == 0)
                        dat[ichange] = newval
                        if (~test.any()):
                           break

        return dat


    ### exit if darray is a dataset.
    if (str(type(darray)) == "xarray.core.dataset.Dataset"):
        print("this function doesn't accept datasets, convert to data array")
        sys.exit()

    ###if it's an xarray dataset, set up the dimensions
    try:
        dims = darray.dims
        if nsamples is None:
            nsamples = darray[dims[0]].size

        nmemin = darray[dims[0]].size


        dimboot = [nsamples*nboots]
        dimboot2d = [nboots, nsamples]
        bootcoords = [('iboot', np.arange(0,nboots,1)), ('isample', np.arange(0,nsamples,1))]
        for icoord in range(1,len(dims)):
            dimboot.append(darray[dims[icoord]].size)
            dimboot2d.append(darray[dims[icoord]].size)
           # bootcoords.append( (dims[icoord], darray[dims[icoord]] ))
            bootcoords.append( (dims[icoord], np.array(darray[dims[icoord]])) )
        #print("you are using an xarray dataarray")

    except:
        if nsamples is None:
            nsamples = darray.shape[0]
        nmemin = darray.shape[0]

        dimboot = [nsamples*nboots]
        dimboot2d = [nboots, nsamples]
        for icoord in range(1,len(darray.shape)):
            dimboot.append(darray.shape[icoord])
            dimboot2d.append(darray.shape[icoord])

        #print("you are using a numpy array")

    ### generate random number for bootstrapping
    if (seed):
        np.random.seed(seed)

    ### do the resampling
    ranu = np.random.uniform(0,nmemin,nboots*nsamples)
    ranu = np.floor(ranu).astype(int)

    if (resample == False):
        ranu_reshape = ranu.reshape([nboots, nsamples])
        undup = [ resolve_duplicates(ranu_reshape[i,:]) for i in np.arange(0,nboots,1)]
        ranu = ranu_reshape.reshape([nboots*nsamples])

    bootdat = np.array(darray[ranu])
    bootdat = bootdat.reshape(dimboot2d)

    #print(bootdat)

    try:
        bootdat = xr.DataArray(bootdat, coords=bootcoords)
    except:
        pass

    return bootdat



def bootgenchunk_multimem(darray, nyears, nmems, nboots=1000, seed=None):
    """Generate nboot samples with nmems members containing chunks of length nyears"""

    ### exit if darray is a dataset.
    if (str(type(darray)) == "xarray.core.dataset.Dataset"):
        print("this function doesn't accept datasets, convert to data array")
        sys.exit()

    ###if it's an xarray dataset, set up the dimensions
    try:
        dims = darray.dims
        nmemin = darray[dims[0]].size

        dimboot = [nyears*nmems*nboots]
        dimboot2d = [nboots, nmems, nyears]
        bootcoords = [('iboot', np.arange(0,nboots,1)), ('imem', np.arange(0,nmems,1)), ('isample', np.arange(0,nyears,1))]
#        bootcoords={'iboot': np.arange(0,nboots,1), 'imem':np.arange(0,nmems,1), 'isample':np.arange(0,nyears,1)}

        for icoord in range(1,len(dims)):
            dimboot.append(darray[dims[icoord]].size)
            dimboot2d.append(darray[dims[icoord]].size)
            bootcoords.append( (dims[icoord], darray[dims[icoord]] ))
            #bootcoords[dims[icoord]] = darray[dims[icoord]]

#        print("you are using an xarray dataarray")

    except:
        nmemin = darray.shape[0]

        dimboot = [nyears*nboots]
        dimboot2d = [nboots, nyears]
        for icoord in range(1,len(darray.shape)):
            dimboot.append(darray.shape[icoord])
            dimboot2d.append(darray.shape[icoord])

        print("you are using a numpy array")

    ### generate random number for bootstrapping
    if (seed):
        np.random.seed(seed)

    ### do the resampling
    ranu = np.random.uniform(0,nmemin-nyears,nboots*nmems)
    ranu = np.floor(ranu).astype(int)

    bootdat = np.zeros(dimboot2d)
    for iboot in np.arange(0,nboots,1):
        for imem in np.arange(0,nmems,1):
            #print(np.shape(darray[ranu[iboot*nmems + imem]:ranu[iboot*nmems+imem]+nyears]))
            bootdat[iboot,imem,...] = darray[ranu[iboot*nmems + imem]:ranu[iboot*nmems+imem]+nyears]


#    bootdat = np.array(darray[ranu])
#    bootdat = bootdat.reshape(dimboot2d)

#    print(bootdat)
#    print(bootcoords)

    #print(bootcoords)
    #bootdat = xr.DataArray(bootdat, coords=bootcoords)

    try:
        bootdat = xr.DataArray(bootdat, 
                coords=[bootcoords[i][1] for i in np.arange(0,len(bootcoords),1)],
                dims=[bootcoords[i][0] for i in np.arange(0,len(bootcoords),1)]) 
    except:
        pass

    return bootdat

def boot_corcoefs(a1, a2, nboots=1000):
    """ Output bootstrap samples of correlation coefficients """
    if (a1.size != a2.size):
        print("The two arrays must have the same size")
        sys.exit()

    samplesize = a1.size
    ranu = np.random.uniform(0,samplesize,nboots*samplesize)
    ranu = np.floor(ranu).astype(int)

    bootdat = np.zeros([samplesize,nboots])
    bootdat1 = np.array(a1[ranu])
    bootdat2 = np.array(a2[ranu])
    bootdat1 = bootdat1.reshape([samplesize,nboots])
    bootdat2 = bootdat2.reshape([samplesize,nboots])

    bootdat1 = xr.DataArray(bootdat1, dims=['model','boot'])
    bootdat2 = xr.DataArray(bootdat2, dims=['model','boot'])

    rvals = xr.corr(bootdat1, bootdat2, dim='model')

    return rvals


def bootdif2means(dat1, dat2, nboots=1000):
    """Obtain the significance of the difference between two means using bootstrapping """
    dat1boot = bootgen(dat1, nboots=nboots)
    dat2boot = bootgen(dat2, nboots=nboots)

    dat1bootm = dat1boot.mean('isample')
    dat2bootm = dat2boot.mean('isample')

    diff = dat2bootm - dat1bootm
    diffmin = diff.quantile(0.025, dim='iboot')
    diffmax = diff.quantile(0.975, dim='iboot')

    dimsignif = diffmin.dims
    coordsignif = diffmin.coords

    signif = diffmin*0+1
    signif = signif.where( (diffmin < 0) & (diffmax > 0), nan)

    return signif


