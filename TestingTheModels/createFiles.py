from createData import runPdrs
from pathlib import Path

###
# Want to automate the input files
###

# Need to open files, have a couple of paramters, then write into 6 files, then close

def makeOneSetOfFiles(nh3_comp, h2_comp):
    global pdrsType

    fuel_composition = {"NH3": nh3_comp, "H2": h2_comp}

    input_directory = f"/home/ns1962/MyWorkspace/TestingTheModels/input/"
    output_directory = f"/home/ns1962/MyWorkspace/TestingTheModels/output/"
    fileDir = ""


    numberOfGridPoints = 255
    reference_species = "H2O"
    fuel_species = list(fuel_composition.keys())
    equivalenceRatios = [0.7, 1.0, 1.4]
    diss_rate = "1.0E+01"
    lewisComment = "#"

    fuelType = ""
    if fuel_composition["NH3"] > 0 and fuel_composition["H2"] > 0: fuelType = "Cracked"
    elif fuel_composition["NH3"] > 0: fuelType = "NH3"
    elif fuel_composition["H2"] > 0: fuelType = "H2"
    fileDir += model + "/" + fuelType + "/"
    if (fuelType == "Cracked"): fileDir += f"{fuel_composition['NH3']}-{fuel_composition['H2']}/"

    modelToFiles = {"Gotama": {"Mech": "/home/ns1962/MyWorkspace/TestingTheModels/gotama_fortran/nh3_h2_gotama_fortran/nh3h2gotama_noAR.chmech", "Thermo": "/home/ns1962/MyWorkspace/TestingTheModels/gotama_fortran/nh3_h2_gotama_fortran/nh3h2gotama_noAR.chthermo", "Trans": "/home/ns1962/MyWorkspace/TestingTheModels/gotama_fortran/nh3_h2_gotama_fortran/nh3h2gotama_noAR.chtrans"},
                    "Glarborg": {"Mech": "/home/ns1962/MyWorkspace/TestingTheModels/glarborg/nh3_h2_glarborg/glarborg_chem.txt", "Thermo": "/home/ns1962/MyWorkspace/TestingTheModels/glarborg/nh3_h2_glarborg/glarborg_thermo.txt", "Trans": "/home/ns1962/MyWorkspace/TestingTheModels/glarborg/nh3_h2_glarborg/glarborg_transport.txt"},
                    "SanDiego": {"Mech": "/home/ns1962/MyWorkspace/TestingTheModels/sandiego_reduced/nh3_h2_sandiego_reduced/first_edit/NOXsandiego20180723_mechCK.txt", "Thermo": "/home/ns1962/MyWorkspace/TestingTheModels/sandiego_reduced/nh3_h2_sandiego_reduced/first_edit/sandiego20160815_therm.txt", "Trans": "/home/ns1962/MyWorkspace/TestingTheModels/sandiego_reduced/nh3_h2_sandiego_reduced/first_edit/sandiego20160815_trans.txt"},
                    "Mei": {"Mech": "/home/ns1962/MyWorkspace/TestingTheModels/mei/mei_chem.inp", "Thermo": "/home/ns1962/MyWorkspace/TestingTheModels/mei/mei_therm.dat", "Trans": "m/home/ns1962/MyWorkspace/TestingTheModels/mei/ei_tran.dat"}}
    modelToLewisNums = {"Gotama": "1.06149 0.16892 1.01378 0.654755 0.667218 0.282247 0.751042 1.01086 1.01763 0.823705 0.634158 1.02826 1.01339 0.621278 1.31011 1.02085 1.15339 1.2707 1.04472 0.736396 1.18876 1.05322 1.05322 0.667218 1.3795 1.02085 1.56653 1.3795 1.01339 1.56275",
                        "Glarborg": "1.06149 0.282247 1.01378 1.3795 0.16892 0.654755 0.667218 1.01086 0.751042 1.01763 0.823705 0.634158 0.621278 0.736396 1.31011 1.18876 1.05322 1.05322 1.04472 1.01086 1.02085 1.02085 1.01339 1.01339 1.02826 1.3795 1.3795 1.15339 1.56653 1.56275 1.2707",
                        "Mei": ""}
    
    appendix = ""
    if specialCondition == "Lewis":
        appendix = "_Lewis"
        pdrsType = 2
        lewisComment = ""
    elif specialCondition == "HiDiss":
        appendix = "_HiDiss"
        diss_rate = "1.0E+04"
    elif specialCondition == "HiCurv": 
        appendix = "_HiCurv"
        pdrsType = 2
        lewisComment = ""
    elif specialCondition == "LoCurv":
        appendix = "_LoCurv"
        pdrsType = 2
        lewisComment = ""
    else:
        print("ERROR special condition not valid")
        quit()
    ########################################################

    file_name = ""
    atm_turbine_prefix = ""

    for i in range(2):
        if i == 0:
            # ATMOSPHERIC CASES
            pressure = 101325.0 #pascals 
            temperature = 300.0 #K
            atm_turbine_prefix = "Atm"
        if i == 1:
            # TURBINE CASES
            pressure = 2.027E+06 #pascals 
            temperature = 700.0 #K
            atm_turbine_prefix = "Turbine"
        # if i == 0:
        #     # COLD TURBINE CASES
        #     pressure = 2.027E+06 #pascals 
        #     temperature = 300.0 #K
        #     atm_turbine_prefix = "ColdTurbine"

        for eqRatio in equivalenceRatios:
            print(f"EQUIVALENCE RATIO: {eqRatio}, {atm_turbine_prefix.upper()}, {specialCondition}")
            if not (fuelType == "Cracked"):
                file_name = f"{fuelType}_{model}{atm_turbine_prefix}_E{str(eqRatio)[0]}-{str(eqRatio)[2]}{appendix}"
            else:
                file_name = f"{fuelType}_{fuel_composition['NH3']}-{fuel_composition['H2']}_{model}{atm_turbine_prefix}_E{str(eqRatio)[0]}-{str(eqRatio)[2]}{appendix}"
            print(file_name)
            # Specify your directory path
            dir_path = Path(f"{input_directory}{fileDir}"[:-1])

            # Create the directory safely
            dir_path.mkdir(parents=True, exist_ok=True)

            with open(f"{input_directory}{fileDir}{file_name}", "w") as f:
                f.write(f"""# MECHANISM AND THERMODYNAMIC DATA ###########################################

Mechanism file :             {modelToFiles[model]["Mech"]}
Thermodata file :            {modelToFiles[model]["Thermo"]}
Transdata file :             {modelToFiles[model]["Trans"]}

Mechanism format : CK

# DISSRATE DATA ##############################################################
#File for dissrate : .false.
#Dissrate file : /scratch/gpfs/MUELLER/srzepka/ICNC24_data/20nh3/20nh3_r218_pdrs_chi.txt
#File for curvature : .false.
#Curvature file : /scratch/gpfs/MUELLER/srzepka/ICNC24_data/20nh3/20nh3_r218_pdrs_kappa.txt
#Grid in files : 48

# MANIFOLD TYPE ###############################################################

Manifold type :              Lambda

# INITIAL CONDITIONS ##########################################################

Pressure :           {pressure}

Oxidizer temperature :           {temperature}
Oxidizer composition :           O2    0.2328821
                                N2    0.7671179

Fuel temperature :           {temperature}
Fuel composition :           NH3    {fuel_composition['NH3']/100}
                            H2    {fuel_composition['H2']/100}

Fuel species :           {fuel_species[0]}
                        {fuel_species[1]}

Equivalence ratio :           {eqRatio}

#Mixture fraction :           N/A

Scalar dissipation rate :            {diss_rate}

#Curvature :              -185.19

# LN listed in order of species in Thermo data file:
{lewisComment}Lewis Numbers : {modelToLewisNums[model]}
#Lewis Tuning : 1.0

# GRID ##########################################################################

Number of grid points :           {numberOfGridPoints}
#Grid stretching type :      power
#Stretching factor :         0.8

Reference species :              H2O
#Start profile :              r433_files/june/TD_0.0.Y

Relative tolerance :             1.0e-6
Absolute tolerance :             1.0e-12

End time :           1.0

Use steady :             .false.

Solver :             0
Iterations :             10000

# OUTPUT #########################################################################

Output directory :           {output_directory}{fileDir}
Pick Output Name :           .true.
Output Name :           {file_name}

Data overwrite:            .true.

Write to screen :            .true.
Write mass fractions :           .true.
Write mole fractions :           .true.
Write flamelet file :            .true.
                    """)
            runPdrs(f"input/{fileDir}{file_name}", pdrsType)
    ########################################################



###################################################################################################3
model = ""
models = ["Glarborg"]#"Gotama", "Mei"] #, "SanDiego"]

# while model not in models:
#     model = input("Model: ")

specialCondition = ""
specialCondition = input("Special conditions (add lewis numbers, curvature, dissipation?): ")

fuel_comps = [{"NH3": 0.9, "H2":0.1}, {"NH3": 0.85, "H2":0.15}, {"NH3": 0.8, "H2": 0.2}, {"NH3": 0.7, "H2":0.3}, {"NH3": 0.6, "H2":0.4}, {"NH3": 0.4, "H2": 0.6}, {"NH3": 0.2, "H2": 0.8}, {"NH3": 0.1, "H2": 0.9}, {"NH3": 0.05, "H2": 0.95}] #{{"NH3": 0, "H2": 1}, {"NH3": 1, "H2": 0}, {"NH3": 0.95, "H2":0.05}, {"NH3": 0.01, "H2": 0.99}

pdrsType = 1

for currModel in models:
    model = currModel
    for fuel_comp in fuel_comps:
        print(f"%%%%%%%%%%%%%%%%%%%%%%%%%%%%  MAKING [{model}]: {fuel_comp["NH3"]*100}%NH3, {fuel_comp["H2"]*100}%H2  %%%%%%%%%%%%%%%%%%%%%%%%%%%%")
        makeOneSetOfFiles(int(float(fuel_comp["NH3"])*100), int(float(fuel_comp["H2"])*100))

# fuel_composition = {"NH3": 0, "H2": 0} # 1 and 99 (will convert to decimals after)
# while fuel_composition["NH3"] + fuel_composition["H2"] != 100:
#     fuel_composition["NH3"] = int(float(input("NH3 Mole Fraction: ")) * 100)
#     fuel_composition["H2"] = int(float(input("H2 Mole Fraction: ")) * 100)

# makeOneSetOfFiles(fuel_composition["NH3"], fuel_composition["H2"])
###################################################################################################3
