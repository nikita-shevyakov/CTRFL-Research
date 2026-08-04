# Here are some examples of how to use some python utilities for pdrs
# ** The examples do not cover the full functionality **

# Load python using "module load anaconda"
# Run python "python"

# Import the libraries for modifying pdrs files
# To be able to import these from anywhere, add the line below to your ~/.bashrc
# and run "source ~/.bashrc"
# add to bashrc -> "export PYTHONPATH=$PYTHONPATH:/home/<your username>/PDRs/src/utilities"
import gen_2d_profile as gen2d
import pdrs_data_file as pdf

# Import some other useful libraries
import numpy as np
import matplotlib.pyplot as plt
import os

# This is a directory on tiger containing some 1D (Z, H2) pdrlets
directory = "/scratch/gpfs/baperry/pdrs/h2/zeta-upper/"

######## EXAMPLE of gen_2d_profile function ##########

# Generate the list of files
zpdrlet_files = [directory + pfile for pfile in os.listdir(directory) if pfile.endswith('.Y')]

# create the 2D pdrlet from the 1D profiles. It's that simple.
# The 2d pdrlet will be saved to a file automatically
# The output of the function is an instance of the pdrs_data_file class (see below)
# Reference species and weights can be a list
# Zgrid and Lgrid are optional
pdrlet2d = gen2d.gen_2d_startprofile(zpdrlet_files,               # input files
                                     'pdrlet2d.Y',                # filename to save
                                     ['Y-H2O'],                   # reference species
                                     [1.0],                       # reference species weights
                                     Zref=0.1,                    # reference Z value
                                     Zgrid=np.linspace(0,1,102),  # output Z grid
                                     Lgrid=np.linspace(0,1,102))  # output L grid


######## EXAMPLE of pdrs_data_file class ##########

# Usually, you instantiate the pdrs_data_file class by reading in a file
# Note: this is not actually necessary here because we already have the output of the
#       gen_2d_startprofile function
# Note: Instances fo the class can also be constructed from raw arrays (see source code)
pdrlet2d = pdf.pdrs_data_file('pdrlet2d.Y')

# Print some data and save a copy of the unedited file
pdrlet2d.rewrite('pdrlet2d_unedited.Y')
pdrlet2d.print_metadata()

# Now that we have loaded in the pdrlet, we can do some plotting
pdrlet2d.plot_variable('Y-H2O') # saved to Y-H2O.eps by default
pdrlet2d.plot_variable('T[K]',filename='T',fileformat='png') #saved to T.png
pdrlet2d.plot_variable('mdotL/rho[1/s]',savefig=False,show=True) # just show on the screen

# For more advanced plotting, extract the data
plt.figure()
plt.contourf(pdrlet2d.get_axis('Z'),
             pdrlet2d.get_axis('L'),
             pdrlet2d.get_variable('Y-O2') + pdrlet2d.get_variable('Y-H2'))
plt.show()

# Maybe we just want to know the value of a variable at a some specific locations
# (Z=0.0289,L=1) and (Z=0.0289,L=0.5)
print ('three places', pdrlet2d.get_variable('T[K]',locs=[[0.0289,1],[0.0289,0.5],[1,0.0289]]))
print ('one   place ', pdrlet2d.get_variable('T[K]',locs=[0.0289,1]))

# Rename a variable
pdrlet2d.rename_variable('Y-H2O','Y-Water')

# Delete some variables
pdrlet2d.delete_variable(['Y-HO2','Y-N2'])

# reset the value of a variable 
pdrlet2d.reset_variable('Y-H2O2',0.00001)
pdrlet2d.reset_variable('Y-H',2.0*pdrlet2d.get_variable('Y-H'))

# Add a new variable in the 6th position
newvalues = np.zeros(pdrlet2d.axescounts)
pdrlet2d.add_variable('Y-CH4', newvalues, 5)

# Save our modified file, and print some data about it
pdrlet2d.rewrite()
pdrlet2d.print_metadata()

# Make slice at a constant value of Z
pdrlet1da = pdrlet2d.make_slice('Z',0.0289)
pdrlet1db = pdrlet2d.make_slice('Z',0.0289)

# Interpolate one of the slices and make a comparison plot
pdrlet1da.interpolate_axis('L',np.linspace(0,1,16))
plt.figure()
plt.plot(pdrlet1db.get_axis('L'),pdrlet1db.get_variable('Y-Water'),'+')
plt.plot(pdrlet1da.get_axis('L'),pdrlet1da.get_variable('Y-Water'),'o')
plt.show()


