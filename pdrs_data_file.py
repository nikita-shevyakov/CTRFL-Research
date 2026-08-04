import numpy as np
from scipy.interpolate import interp1d, RegularGridInterpolator
from itertools import cycle
import matplotlib.pyplot as plt

# Python class for reading and editing PDRs data files
# Everything should apply for pdrlets of arbitrary dimensionality (1,2,3, or more!)
#
# Contains the following functions:
# -For accessing data
#   (1) get_variable
#   (2) get_axis
#   (3) calc_ref_dissrates
#   (4) print_metadata
#   (5) plot_variable
# -For editing data
#   (1) interpolate_axis
#   (2) rename_variable
#   (3) delete_variable
#   (4) add_variable
#   (5) reset_variable
#   (6) make_slice
#   (7) rewrite
#
# Directions: Instantiate the class based on either an existing file or manual insertion of data,
#             then use the functions to access the data for postprocessing or editing the data. Once
#             you have made your desired changes, call rewrite() to save the changes to a file
#
# Here are some key attributes of the class:
# * fname: the name of the file (string)
# * manifoldvars: the variables that parameterize the pdrlet/manifold, an array in the order from the file
# * ndims: the number of manifoldvars (integer)
# * axescounts: array containing the number of points in the manifold for each manifold variable
# * axes: the grid locations for each manifold variable (array of arrays)
# * datavars: the chis and thermochemical variables (Y_k,T,etc) from the pdrlet
# * nvars: the number of datavars (integer)
# * data: array containing the values of all the datavars at each point in the manifold
#         important note: this is an array of dimension ndims+1. The first ndims correspond to the manifoldvars
#         in REVERSE order as they are listed in the manifoldvars array which is why there are many [::-1] calls
#         (sorry about this!). The final dimension corresponds to the datavars, in order. 
#
# IMPORTANT: 
# This class requires up to date versions of numpy and scipy.
# Try "module load anaconda" to make sure you have these.

class pdrs_data_file(object) :

    # generate a datafile by reading in (default) or based on specified data
    def __init__(self, fname=None, fromdata=False,
                       manifoldvars=None,
                       datavars=None,
                       axes=None,
                       data=None) :

        # read pdrs file
        if not fromdata :
            if fname == None:
                raise RuntimeError("no data file was specified")
            if manifoldvars is not None or axes is not None or data is not None or datavars is not None:
                raise RuntimeError("cannot specify manifoldvars, axes, or data when generating from a file")
            self.fname = fname
            data = np.genfromtxt(fname,skip_header=1)
            npoints_tot, self.nvars = data.shape
            infile = open(fname,'r')
            headers = infile.readline()
            infile.close()
            headers = [headers[i:i+20].strip() for i in range(0,len(headers),20) ]
            headers = headers[:-1]

            # determine what type of pdrlet is being examined (Z, L, H, ZL, ZH, LH, ZLH)
            # manifold variables must be in the first columns of pdrlet files
            manifoldvars = ('Z','L','H','F')
            self.manifoldvars = []
            for var in manifoldvars:
                if var in headers :
                    self.manifoldvars.append(var)
            self.ndims = len(self.manifoldvars)
            self.nvars = self.nvars - self.ndims
            if self.ndims < 1:
                raise RuntimeError("specified file has no valid manifold parameterizing variables")

            # determine axes of the manifoldvars, this is very hacked together. Come up with something better
            # if you are reading this and are not happy with it
            self.axescounts=[0]*self.ndims
            self.axes=[0]*self.ndims
            step = 1
            for idim in range(self.ndims):
                ipoint = 0
                firstentry = data[ipoint,idim]
                self.axes[idim] = [firstentry]
                self.axescounts[idim] = 1
                while not np.isclose(data[ipoint+step,idim], firstentry,atol=1e-11):
                    ipoint += step
                    self.axescounts[idim] += 1
                    self.axes[idim].append(data[ipoint,idim])
                    if (ipoint+step) == npoints_tot: break
                step = step * self.axescounts[idim]

            # split out the rest of the variables and put into a matrix
            self.datavars = headers[self.ndims:]
            self.data = data[:,self.ndims:].reshape(self.axescounts[::-1] + [self.nvars])

        # generate from data
        else :
            self.fname = fname
            self.data = data
            self.manifoldvars = manifoldvars
            self.axes = axes
            self.datavars = datavars

            # generate additional variables and do error checking
            self.ndims = len(manifoldvars)
            if len(self.axes) !=  self.ndims: 
                raise RuntimeError("Number fo manifold vars and axes must agree")
            self.nvars = len(self.datavars)
            self.axescounts = [len(axis) for axis in self.axes]
            if self.data.shape != tuple(self.axescounts[::-1] + [self.nvars]):
                raise RuntimeError("shape of data matrix does not match given axes and variable list")

    # return a single variable as a function of the manifold variables (default),
    # or at specific locations on the manifold (if locs is a matrix of points in manifold space)
    def get_variable(self,tag,locs='all'):
        index = -1
        for ivar, varname in enumerate(self.datavars) :
            if tag == varname :
                index = ivar
                break
        if index < 0 :
            raise RuntimeError("Could not find requested variable: " + tag)
        if locs is 'all':
            return self.data.flatten()[index::self.nvars].reshape(self.axescounts[::-1])
        else :
            interper = RegularGridInterpolator(self.axes[::-1],self.data.flatten()[index::self.nvars].reshape(self.axescounts[::-1]))
            if not np.isscalar(locs[0]): locs = [loc[::-1] for loc in locs]
            if np.isscalar(locs[0]) and self.ndims is not 1: locs = locs[::-1] 
            return interper(locs)

    # return the axis for a given manifold variable
    def get_axis(self,tag):
        index = np.array(self.manifoldvars)==tag
        if sum(index) != 1: raise RuntimeError("Desired axis does not exist or appears more than once")
        index = self.manifoldvars.index(tag)
        return self.axes[index]

    # interpolate the axis for the given manifold variable
    # can either specify the points of the entire axis, or interpolate to a linear grid with specified npoints
    # accepts interpolation methods, 'nearest', 'linear', 'cubic', etc
    def interpolate_axis(self,manifoldvar='only',axisnew=None,npoints=None,interpmethod='linear'):
        # find axis to be interpolated
        if manifoldvar == 'only' and self.ndims ==1 :
            manifoldvar = self.manifoldvars[0]
        elif manifoldvar not in self.manifoldvars :
            raise RuntimeError("You need to request a valid manifold parameterizing variable to interpolate")
        interpaxis = self.manifoldvars.index(manifoldvar)

        # Generate new axis if needed
        if (axisnew is None and npoints is None) or (axisnew is not None and npoints is not None):
            raise RuntimeError("Must specify an axis or number of points, not neither and not both")
        if axisnew is None:
            axisnew = np.linspace(0,1,npoints)
        if npoints is None:
            npoints = len(axisnew)
            
        # train interpolator and interpolate data, overwriting interpolated data replacing old data
        interper = interp1d(self.axes[interpaxis], self.data, axis=self.ndims-1-interpaxis, kind=interpmethod)
        self.data = interper(axisnew)
        self.axes[interpaxis] = axisnew
        self.axescounts[interpaxis] = npoints
 
    # Rename variables (arbitrary number)
    def rename_variable(self,oldname,newname):
        if newname in self.datavars:
            raise RuntimeError("A variable with name '" + newname +"' already exists")
        index = self.datavars.index(oldname)
        self.datavars[index] = newname                
 
    # Delete variables (arbitrary number)
    def delete_variable(self,names):
        if np.isscalar(names): names = [names]
        delvars = [self.datavars.index(name) for name in names]
        self.data = np.delete(self.data,delvars,self.ndims)
        self.datavars = np.delete(self.datavars,delvars).tolist()
        self.nvars = self.nvars - len(delvars)

    # Reset a single variable
    # Default is to reset to 0. Can either specify a scalar for uniform profile, or a full nonuniform profile
    def reset_variable(self,name,value=0):
        index = self.datavars.index(name)
        if np.isscalar(value):
            value = np.full(self.axescounts[::-1],value)
        if value.shape != tuple(self.axescounts[::-1]):
            raise RuntimeError( "Shape of specified values does not match the axes of the pdrlet")
        self.data[ ... , index] = value

    # Add variables (arbitrary number), can optionally specify where they go, default is at the end.
    # all inputs should either be scalar entries, or all should be lists
    # if values are scalars, used for whole domain. can also be arrays covering whole domain with nonconstant values
    def add_variable(self,names,values=0,locs='end'):
        if np.isscalar(names):
            names = [names]
            values = [values]
            if locs is not 'end':
                locs = [locs]
        if locs is 'end':
            locs = range(self.nvars,self.nvars+len(names))
        for name, value, loc in zip(names,values,locs):
            self.datavars = self.datavars[:loc] + [name] + self.datavars[loc:] 
            self.data = np.insert(self.data, loc, value, self.ndims)
        self.nvars += len(names)
        
    # slice out one of the dimensions
    def make_slice(self,slicedir, slicevalue, remove_chis=True):
        if slicedir not in self.manifoldvars:
            raise RuntimeError("Requested slice direction is not one of the manifold dimensions")
        # create a new pdf instance to output
        sliced = pdrs_data_file(fromdata=True,
                                manifoldvars=list(self.manifoldvars),
                                data=self.data,
                                datavars=list(self.datavars),
                                axes=list(self.axes))
        # interpolate_axis actually does the slicing
        sliced.interpolate_axis(manifoldvar=slicedir, axisnew=[slicevalue])
        # we now need to drop out the sliced dimension and the unwanted chis
        slicedir_ind = sliced.manifoldvars.index(slicedir) 
        sliced.manifoldvars.pop(slicedir_ind)
        sliced.axes.pop(slicedir_ind)
        sliced.axescounts.pop(slicedir_ind)
        sliced.data = sliced.data.squeeze(axis=sliced.ndims-slicedir_ind-1)
        sliced.ndims = sliced.ndims-1
        if remove_chis:
            deletevars = []
            for datavar in sliced.datavars:
                if 'Chi' in datavar and slicedir in datavar:
                    deletevars.append(datavar)
                elif 'Chi' in datavar and (sliced.ndims==1):
                    sliced.rename_variable(datavar,'Chi[1/s]')
                elif 'mdot' in datavar and slicedir in datavar:
                    deletevars.append(datavar)
            sliced.delete_variable(deletevars)
        return sliced

    # calculate reference dissipation rates
    def calc_ref_dissrates(self,reference_vals=None):
        if reference_vals is None:
            reference_vals = 0.5 * np.ones(self.ndims)
        if len(reference_vals) != self.ndims: raise RuntimeError("Incorrect number of reference values specified")
        # find and evaluate chis
        chinames = []
        chivals  = {}
        for var in self.datavars:
            if 'Chi' in var:
                chinames.append(var)
                chivals[var] = self.get_variable(var,locs=reference_vals)
        return chinames, chivals
    
    # print out the modified data file
    # (overwrites the file be default, generates a new file if fname_new is specified)
    def rewrite(self,fname_new=None) :
        if fname_new is None and self.fname is not None: 
            fname_new = self.fname
        elif fname_new is None:
            raise RuntimeError("Cannot write pdrs file because no filename has been given")
        outfile = open(fname_new,'w')

        # write headers
        string = ''
        for header in self.manifoldvars + self.datavars :
            string = string + '{:>20s}'.format(header)
        string = string + '\n'
        outfile.write(string)

        # write grid and data, use idexes to loop over all manifold variables
        idexes = [0] * self.ndims
        done = False
        datacycle = cycle(self.data.ravel())
        while not done:
            pointer = 0
            string = ''
            for ii,axis in enumerate(self.axes):
                string = string + '{:20.12E}'.format(axis[idexes[ii]])
            for ii in range(self.nvars):
                string = string + '{:20.12E}'.format(next(datacycle))
            string = string + '\n'
            idexes, done, pointer = recurse_aug(idexes, self.axescounts, pointer, done)
            outfile.write(string)
            # leave a space between sections of data
            if pointer is not 0:
                outfile.write('\n')

    # print metadata to screen
    def print_metadata(self,reference_vals=None,print_chis=True,print_minmax=True):
        # Basic Data
        print ('')
        print (str(self.ndims) + "D " + "".join(self.manifoldvars) + " pdrlet")
        if self.fname is not None:
            print ('{:20s}'.format("PDRs datafile: ") + self.fname)
        else:
            print ("PDRs datafile (unsaved)")
        print ('{:20s}'.format("Grid: ") + " x ".join([str(count) for count in self.axescounts]))
        print ('{:20s}'.format("Number of variables: ") + str(self.nvars))
        # Reference Chis
        if print_chis:
            chinames, chivals = self.calc_ref_dissrates(reference_vals)
            print ("Reference chis:")
            for chiname in chinames:
                print ('{:>20s}'.format(chiname) + ': ' + '{:10.2E}'.format(chivals[chiname][0]))
        # Variables min/max
        if print_minmax:
            print ('')
            print ("Variables (min, max):")
            for var in self.datavars:
                vals = self.get_variable(var)
                minval = np.min(vals)
                maxval = np.max(vals)
                print ('{:>20s}'.format(var) + ' ('+ '{:20.12E}'.format(minval) + ',' + '{:20.12E}'.format(maxval) + ' ) ')
        else :
            print ('')
            print ('{:20s}'.format("Variables: ") + " ".join(self.datavars))

    # Make a plot of a variable (quick plotting, not production plots)
    # filename optionally specifies the name of the plot file that will be saved. 
    # Works for 1D pdrlets (line plots) or 2D pdrlets (contour plots)
    def plot_variable(self,variable='T[K]',filename=None, fileformat='eps', contour=True, show=False, savefig=True):
        if filename is None:
            filename=variable
        filename = filename + '.' + fileformat
        fig =plt.figure()
        if self.ndims is 1:
            plt.xlabel(self.manifoldvars[0])
            plt.ylabel(variable)
            plt.plot(self.get_axis(self.manifoldvars[0]),
                     self.get_variable(variable))
        elif self.ndims is 2:
            plt.xlabel(self.manifoldvars[0])
            plt.ylabel(self.manifoldvars[1])
            if contour:
                filled = plt.contourf(self.get_axis(self.manifoldvars[0]),
                                      self.get_axis(self.manifoldvars[1]),
                                      self.get_variable(variable),
                                      50)
            else:
                filled = plt.pcolor(self.get_axis(self.manifoldvars[0]),
                                    self.get_axis(self.manifoldvars[1]),
                                    self.get_variable(variable))
            cbar = fig.colorbar(filled)
            cbar.set_label(variable)
        else:
            raise RuntimeError("Plotting only supported for one and two dimensional pdrlets")
        if show:
            plt.show()
        if savefig:
            plt.savefig(filename)
            plt.close()
            
# function to recursively augment indices, like an odometer
# augments first index, second index if 1st loops over, etc
def recurse_aug(idexes, lens, pointer, done):
    if idexes[pointer] < lens[pointer]-1:
        idexes[pointer] += 1
    elif pointer < len(idexes)-1:
        idexes[pointer] = 0
        idexes, done, pointer = recurse_aug(idexes, lens, pointer +1, done)
    else : 
        done = True
    return idexes, done, pointer

# Class that claculates Lambda based on a 2D ZL pdrlet
class lambda_calculator(object):

    # Initialize - can initialize from file or an existing 2D ZL pdrlet object
    def __init__(self, pdrlet2d, refspec, refspec_weights=None):
        if isinstance(pdrlet2d, str):
            pdrlet2d = pdrs_data_file(pdrlet2d)
        elif isinstance(pdrlet2d,pdrs_data_file):
            pdrlet2d = pdrlet2d
        else:
            raise RuntimeError('Must give filename or instance pdr pdrs_data_file class')

        print (pdrlet2d.manifoldvars)
        if not np.array_equal(pdrlet2d.manifoldvars, ['Z','L']):
            raise RuntimeError('2d Pdrlet must be a ZL pdrlet')

        # Calculate Yref(Z,L)
        self.refspec = refspec
        self.refspec_weights = refspec_weights
        self.Yref = calculate_Yref(pdrlet2d, refspec, refspec_weights)
        self.Zvals   = pdrlet2d.get_axis('Z')
        self.Lambdas = pdrlet2d.get_axis('L')
            
    # return a vactor of Lambda corresponding to the specified Zs and Yrefs
    def calculate(self,Yrefs, Zs):
        if len(Yrefs) != len(Zs) :
            raise RuntimeError("Must give same number of Zs and Yrefs")
        Ls = np.zeros(len(Yrefs))
        for ii in range(len(Yrefs)):
            Zval = Zs[ii]
            Yref = Yrefs[ii]
            ZlocRight =max(min(np.searchsorted(self.Zvals,Zval),len(self.Zvals)-1),1)
            ZlocLeft = ZlocRight - 1
            alpha = (Zval - self.Zvals[ZlocLeft])/(self.Zvals[ZlocRight]-self.Zvals[ZlocLeft])
            LvalLeft = np.interp(Yref,self.Yref[:,ZlocLeft] ,self.Lambdas,left=0.0,right=1.0)
            LvalRight= np.interp(Yref,self.Yref[:,ZlocRight],self.Lambdas,left=0.0,right=1.0)
            Ls[ii] = LvalLeft + (LvalRight - LvalLeft)*alpha
        return Ls

# Function that calculates Yref on a pdrlet
def calculate_Yref(pdrlet,refspec,refspec_weights):
    if refspec_weights is None:
        refspec_weights = np.ones(len(refspec))
    Yref = np.zeros(pdrlet.axescounts[::-1])
    for spec, weight in zip(refspec, refspec_weights):
        Yref += weight*pdrlet.get_variable(spec)
    return Yref

# read in FlameMaster .kg file and convert it to PDRs .Y file
# fmtype can be either 'nonpremixed' (Z-space counterflow) or 'premixed' (physical space planar flame)
# function returns a pdrlet object, also writes it to a file if outfilename is specified
# if Lambda calculator and Zvalue are specified, calculates the real Lambda for premixed case
# Lambda calculator is an instance of the lambda_calculator class, Zvalue is the value of Z
# or Zstoich if phi is in the kgfile name.
def read_kg(kgfile,fmtype,LambdaCalculator=None,Zvalue=None,outfilename=None):

    # get headers
    with open(kgfile) as kgfi:
        kgfi.readline()
        headers = kgfi.readline()
    headers = headers.strip().split("\t")
    # eliminate spaces and truncate to 19 characters
    headers = [header.replace(" ","")[:19] for header in headers]
    # rename temperature
    if 'temperature[K]' in headers: headers[headers.index('temperature[K]')] = 'T[K]'

    # read in data
    data = np.genfromtxt(kgfile,delimiter='\t',skip_header=2)
    
    if fmtype is 'nonpremixed' :
        raise RuntimeError('Nonpremixed .kg files not yet supported')
    elif fmtype is 'premixed':
        # generate a fake Lambda
        nL,nvars = data.shape
        Lgrid = np.linspace(0,1,nL)
        pdrlet = pdrs_data_file(fname=outfilename,
                                fromdata=True,
                                manifoldvars=['L'],
                                datavars = headers,
                                axes=[Lgrid],
                                data = data)

        # move any variable that appears ahead of temperature to the end of the file
        move_vars = pdrlet.datavars[:pdrlet.datavars.index('T[K]')]
        for var in move_vars:
            tmp = pdrlet.get_variable(var)
            pdrlet.delete_variable(var)
            pdrlet.add_variable(var, tmp)

        # rename Mass fractions
        for var in pdrlet.datavars:
            if 'massfraction-' in var:
                pdrlet.rename_variable(var,var.replace('massfraction-','Y-'))
            
        # add in Chi at first location
        pdrlet.add_variable('Chi_LL[1/s]',0,0)
        
        # get real Lgrid and substitute it
        if LambdaCalculator is not None:
            # Get the value of Z
            if 'phi' in kgfile:
                ind = kgfile.index('phi') + 3
                phi = float(kgfile[ind] + '.' + kgfile[ind+2:ind+6])
                Zvalue = phi/(1+(1-Zvalue)/Zvalue)
                print ('Using Z calculated based on Zstoich and phi from filename')
            Yref = calculate_Yref(pdrlet,LambdaCalculator.refspec,LambdaCalculator.refspec_weights)
            Lgrid = LambdaCalculator.calculate(Yref,(Zvalue*np.ones(len(Yref))).tolist()).tolist()

            # put in new grid
            pdrlet.axes[0] = Lgrid

            # also add in the correct chi
            chis = np.zeros(len(Lgrid))
            yvals = pdrlet.get_variable('y[m]')
            diffs = pdrlet.get_variable('lambda[W/m]')
            diffs /= pdrlet.get_variable('density')
            diffs /= pdrlet.get_variable('cp[J/m^3K]')
            for ii in range(1,len(chis)-1):
                chis[ii] = (Lgrid[ii+1] - Lgrid[ii-1])/(yvals[ii+1]-yvals[ii-1])
            chis = 2 * diffs * chis**2
            pdrlet.reset_variable('Chi_LL[1/s]',chis)
            
            # deal with badness of kg files
            LgridNew = [Lval for Lval in Lgrid if not np.isclose(Lval, 1.0, atol=1e-7)]
            LgridNew = LgridNew + np.linspace(1.0-1e-7,1,len(Lgrid) - len(LgridNew)).tolist()
            Lgrid = LgridNew
            LgridNew = [Lval for Lval in Lgrid if not np.isclose(Lval, 0.0, atol=1e-9)]
            LgridNew =  np.linspace(0,1e-9,len(Lgrid) - len(LgridNew)).tolist() + LgridNew
            Lgrid = LgridNew
            pdrlet.axes[0] = Lgrid
    else:
        raise RuntimeError('Invalid flamemaster simulation type specified')

    # Delete mole fractions, ProdRate, other undersireables
    delete_vars  = [var for var in headers if var.startswith('X-')]
    delete_vars += [var for var in headers if var.startswith('molefraction-')]
    if len(delete_vars) > 0: pdrlet.delete_variable(delete_vars)
    
    if outfilename is not None:
        pdrlet.rewrite()
    
    return pdrlet


class premixed_interpolator(object):

    # works only for 1d premixed pdrlet input
    def __init__(self,listoffiles,refspec,refspec_weights):
        self.refspec = refspec
        self.refspec_weights = refspec_weights
        # sort the list of files, low to high chi
        chis = [float(fi[fi.index('CHILL')+5:fi.index('CHILL')+12]) for fi in listoffiles]
        listoffiles = [fi for _,fi in sorted(zip(chis,listoffiles))] 
        
        # read in first pdrlet to get som parameters
        self.pdrlet = pdrs_data_file(listoffiles[0])
        self.data = np.zeros( (len(listoffiles),)+self.pdrlet.data.shape)
        for ii,fi in enumerate(listoffiles) :
            pdrlet = pdrs_data_file(fi)
            self.data[ii,:,:] = pdrlet.data
        ind_chi = self.pdrlet.datavars.index('Chi_LL[1/s]')
        self.yref = calculate_Yref(self.pdrlet,refspec,refspec_weights)
        # create an interpolator for each value of Yref
        self.interpolators=[]
        for ii in range(len(self.yref)):
            interper = interp1d(self.data[:,ii,ind_chi], self.data[:,ii,:],axis=0,bounds_error=False,
                                fill_value=(self.data[0,ii,:],self.data[-1,ii,:]))
            self.interpolators.append(interper)
            
    def interpolate(self,pdrlet_in,outfilename=None):
        if type(pdrlet_in) is not type(self.pdrlet):
            print (pdrlet_in)
            pdrlet_in = pdrs_data_file(pdrlet_in)
        yref_in = calculate_Yref(pdrlet_in, self.refspec, self.refspec_weights)
        data_out = np.zeros((len(yref_in),self.pdrlet.nvars))
        ny = len(self.yref)
        for ii,yrin in enumerate(yref_in) :
            chi = pdrlet_in.data[ii,0]
            iabove= np.searchsorted(self.yref,yrin)
            iabove = min(iabove,ny-1)
            ibelow=  iabove-1
            ibelow= max(ibelow,0)
            alpha = (yrin - self.yref[ibelow])/(self.yref[iabove]-self.yref[ibelow])
            valsabove = self.interpolators[iabove]([chi])
            valsbelow = self.interpolators[ibelow]([chi])
            data_out[ii,:] = valsbelow + alpha*(valsabove - valsbelow)

        data_out = np.nan_to_num(data_out,0.0)
        print (data_out.shape)
        print (len(self.pdrlet.datavars))
        print (self.pdrlet.axescounts)
        pdrlet_out = pdrs_data_file(fname=outfilename,
                                    fromdata=True,
                                    manifoldvars=['L'],
                                    datavars = self.pdrlet.datavars,
                                    axes=[yref_in],
                                    data = data_out)
        if outfilename is not None:
            pdrlet_out.rewrite()

        return pdrlet_out
