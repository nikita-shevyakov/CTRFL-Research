#!/bin/python

import numpy as np
import pdrs_data_file as pdf
# not needed for function
import os
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

# Assemble a 2D startprofile for ZL pdrlets out of 1D profiles from Z pdrlets
# * Lambda definition based on either Knudsen / Perry / Mueller (standard Lambda) or Linear
#       for either, reference species mist be specified, weights are optional.
#       for standard definition, Zref should be specified
# * Zgrid can either be specified, in which case the pdrlets do not all need to have the same grid,
#   they will be interpolated to the specified grid. Alternatively, the grid from the nonpremixed PDRlets
#   will be used
# * Lgrid can either be specified, or the grid based on the L values of the pdrlets will be used (for
#   standard lambda). For linear Lambda, Lgrid MUST be specified.
# * Equilibrium should be read in as a pdrlet
def gen_2d_startprofile(zpdrlet_files,
                        outfilename,
                        refspec, 
                        refspec_weights=None,
                        lambda_def='standard', 
                        Zref=0.5,
                        Zgrid=None, 
                        Lgrid=None):

    # Check that the definition of Lambda is allowable
    if lambda_def not in ['standard', 'linear']:
        raise RuntimeError('The definition of Lambda must be the sensible definition or linear') 
    if lambda_def is 'linear' and Lgrid is None:
        raise RuntimeError('Need to specify an L grid for linear Lambda')
    
    # Check that the user specified the right number of reference species weights, put ones as default
    if refspec_weights is None:
        refspec_weights = np.ones(len(refspec))
    if len(refspec_weights) is not len(refspec) :
        raise RuntimeError('Incorrect number of reference species weights specified')
    refspec_weights = dict(zip(refspec,refspec_weights))

    # read in all pdrlets
    nfiles = len(zpdrlet_files)
    pdrlets = [0] * nfiles
    variables = None
    check_z = False
    if Zgrid is None: check_z = True
    for counter, filename in enumerate(zpdrlet_files):

        # read file
        pdrlet = pdf.pdrs_data_file(filename)
        pdrlets[counter] = pdrlet
        
        # Check that the variables are the same
        if variables is None:
            variables = pdrlet.datavars
        else:
            if pdrlet.datavars != variables:
                raise RuntimeError("pdrlets contain different variables/columns")
            
        # Check that the Z grids are the same, or interpolate to a new zgrid
        if check_z and Zgrid is None:
            Zgrid = pdrlet.get_axis('Z')
        elif check_z:
            if not np.allclose(Zgrid, pdrlet.get_axis('Z')):
                raise RuntimeError("pdrlets do not have same Zgrid")
        else:
            pdrlet.interpolate_axis('Z',Zgrid)



    # get Yref,st and rescale to become lambda
    lambdavals = [0.0] * nfiles
    for counter, pdrlet in enumerate(pdrlets):
        for spec in refspec:
            lambdavals[counter] += refspec_weights[spec]*pdrlet.get_variable(spec,locs=[Zref])[0]
    minval = np.min(lambdavals)
    maxval = np.max(lambdavals)
    lambdavals = (lambdavals - minval) / (maxval - minval)

    # sort both pdrlets and lambdavals by their lambdavals
    lambdavals, pdrlets = zip(*sorted(zip(lambdavals,pdrlets)))

    # verify monotonicity
    monotonic = all(l2 > l1 for l1,l2 in zip(lambdavals, lambdavals[1:]))
    if not monotonic:
        raise RuntimeError("Lambda is not monotonic in pdrlets")

    # combine data from the pdrlets
    data = np.zeros((len(lambdavals),len(Zgrid),len(variables)))
    for counter, pdrlet in enumerate(pdrlets):
        data[counter] = pdrlet.data

    # do stuff for standard definition of Lambda
    if lambda_def is 'standard':
        # Generate the 2D pdrlet
        ZLpdrlet =  pdf.pdrs_data_file(fname=outfilename,
                                       fromdata=True,
                                       manifoldvars =['Z','L'],
                                       datavars = variables,
                                       axes=[Zgrid,lambdavals],
                                       data = data)

        # interpolate onto L grid if desired
        if Lgrid is not None:
            ZLpdrlet.interpolate_axis('L',Lgrid)

    # otherwise do stuff for linear lambda
    elif lambda_def is 'linear':
        data_out = np.zeros((len(Lgrid),len(Zgrid),len(variables)))
        # interpolate onto yref grid (different for each value of Z)
        for iz in range(len(Zgrid)):
            YrefIn = np.zeros(len(lambdavals))
            for refspecies in refspec:
                YrefIn = YrefIn + refspec_weights[refspecies]*data[:,iz,variables.index(refspecies)].flatten()
                YrefIn[0] = 0.0 # so interpolation works without adding out of bounds stuff
            YrefOut = YrefIn[0] + np.array(Lgrid) * (YrefIn[-1] - YrefIn[0])
            if YrefIn[0] == YrefIn[-1]:
                YrefIn = np.linspace(0,1,len(YrefIn))
            interper = interp1d(YrefIn, data[:,iz,:], axis=0) # maybe add how to deal with out of bounds?
            data_out[:,iz,:] = interper(YrefOut)
        # Generate the 2D PDRlet
        ZLpdrlet =  pdf.pdrs_data_file(fname=outfilename,
                                       fromdata=True,
                                       manifoldvars =['Z','L'],
                                       datavars = variables,
                                       axes=[Zgrid,Lgrid],
                                       data = data_out)

    # Rename/add chis and mdot
    ZLpdrlet.rename_variable("Chi[1/s]","Chi_ZZ[1/s]")
    ZLpdrlet.add_variable(["Chi_ZL[1/s]","Chi_LL[1/s]"],values=[0,0],locs=[1,2])
    ZLpdrlet.add_variable("mdotL/rho[1/s]",0)
    
    # Save to file
    ZLpdrlet.rewrite()
    return ZLpdrlet
