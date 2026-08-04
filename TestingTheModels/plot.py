import pdrs_data_file as pdf
# import matplotlib
# matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import numpy as np
import pandas as pd


class MultiPlotter():
    def __init__(self, gotama_file, glarborg_file):
        self.gotama_file = gotama_file
        self.gotama_data = pdf.pdrs_data_file(gotama_file)

        self.glarborg_file = glarborg_file
        self.glarborg_data = pdf.pdrs_data_file(glarborg_file)

        # Robust title: parse fuel/condition/phi generically instead of
        # assuming a fixed number of "_"-separated parts.
        import re
        fname = os.path.basename(gotama_file)
        m = re.match(r'(.+)_Gotama(Atm|Turbine)_E(\d)-(\d)', fname)
        if m:
            fuel, condition, e1, e2 = m.groups()
            self.title = f"{fuel} {condition} E{e1}.{e2}: Glarborg vs Gotama"
        else:
            self.title = f"{fname}: Glarborg vs Gotama"

        self.vars = self.gotama_data.datavars
        self.x_axisL_gotama = self.gotama_data.get_axis('L')
        self.x_axisL_glarborg = self.glarborg_data.get_axis('L')  # don't assume shared axis

        self.includedVars = ["Y-OH", "Y-NO2", "Y-NO", "Y-H2", "Y-N2O", "Y-NH3", "Y-H2O"]
        self.gotamaColorOrder = ['maroon', 'red', 'orange', 'yellow', 'peru', 'gold']
        self.glarborgColorOrder = ['midnightblue', 'blue', 'slateblue', 'blueviolet', 'violet', 'purple']

        self.gotamaVarColorPairs = {}
        self.glarborgVarColorPairs = {}
        for i, var in enumerate(self.includedVars):
            if i < len(self.gotamaColorOrder):
                self.gotamaVarColorPairs[var] = self.gotamaColorOrder[i]
                self.glarborgVarColorPairs[var] = self.glarborgColorOrder[i]
        
        self.maxValueDifferencePoint = [] # L, value
        self.maxPercentageDifferencePoint = [] # L, value

        self.percentDifferenceCutoff = 15 #%
        self.bigDifferencePoints = [] # list of tuples

        self.focusedVar = "Y-NO2"

        #self.findBigDifferencePoints(self.focusedVar)
        #self.findMaxPoint(self.focusedVar)

    # finds points that differ the most in value and in percentage across 2 models
    def findMaxPoint(self, var, noise_threshold=1e-6):
        maxGlarborgVal = np.max(self.glarborg_data.get_variable(var))
        maxGotamaVal = np.max(self.gotama_data.get_variable(var))


        # glarborgVar = np.asarray(self.glarborg_data.get_variable(var))
        # gotamaVar = np.asarray(self.gotama_data.get_variable(var))

        # Lg = np.asarray(self.x_axisL_glarborg)
        # Lo = np.asarray(self.x_axisL_gotama)

        # lo, hi = max(Lg.min(), Lo.min()), min(Lg.max(), Lo.max())
        # common_L = np.linspace(lo, hi, max(len(Lg), len(Lo)))
        # glarborg_interp = np.interp(common_L, Lg, glarborgVar)
        # gotama_interp = np.interp(common_L, Lo, gotamaVar)

        # self.maxValueDifferencePoint = [None, None, 0]
        # self.maxPercentageDifferencePoint = [None, None, 0]

        # for i in range(len(common_L)):
        #     gv, ov = glarborg_interp[i], gotama_interp[i]

        #     # max absolute difference point
        #     absDiff = abs(gv - ov)
        #     if absDiff > self.maxValueDifferencePoint[2]:
        #         self.maxValueDifferencePoint = [common_L[i], gv, absDiff]
        #         percentDifference = abs(gv - ov) / ((abs(gv) + abs(ov)) / 2) * 100
        #         self.maxPercentageDifferencePoint = [self.x_axisL_glarborg[i], glarborgVar[i], percentDifference]

            # # max percent difference point (skip noise-level baselines)
            # denom = (abs(gv) + abs(ov)) / 2
            # if denom < noise_threshold:#abs(gv) < noise_threshold and abs(ov) < noise_threshold:
            #     continue
            # percentDifference = abs(gv - ov) / ((abs(gv) + abs(ov)) / 2) * 100
            # if percentDifference > self.maxPercentageDifferencePoint[2]:
            #     self.maxPercentageDifferencePoint = [common_L[i], gv, percentDifference]
            #     if percentDifference > self.maxPercentageDifferencePoint[2]: 
            #         self.maxPercentageDifferencePoint = [self.x_axisL_glarborg[i], glarborgVar[i], percentDifference]

    # finds points that have _>15% differnece_ across models and adds them to list (and that are non neglible)
    def findBigDifferencePoints(self, var, noise_threshold=1e-6):
        glarborgVar = np.asarray(self.glarborg_data.get_variable(var))
        gotamaVar = np.asarray(self.gotama_data.get_variable(var))

        Lg = np.asarray(self.x_axisL_glarborg)
        Lo = np.asarray(self.x_axisL_gotama)  # you'll need this if you don't already have it

        # Interpolate both onto a common grid so indices actually line up,
        # even if the two solvers used different mesh points/counts.
        lo, hi = max(Lg.min(), Lo.min()), min(Lg.max(), Lo.max())
        common_L = np.linspace(lo, hi, max(len(Lg), len(Lo)))
        glarborg_interp = np.interp(common_L, Lg, glarborgVar)
        gotama_interp = np.interp(common_L, Lo, gotamaVar)

        self.bigDifferencePoints = []
        for i in range(len(common_L)):
            gv, ov = glarborg_interp[i], gotama_interp[i]
            # skip points where both values are essentially noise
            denom = (abs(gv) + abs(ov)) / 2
            if denom < noise_threshold:#abs(gv) < noise_threshold and abs(ov) < noise_threshold:
                continue
            percentDifference = abs(gv - ov) / ((abs(gv) + abs(ov)) / 2) * 100
            if percentDifference > self.percentDifferenceCutoff:
                self.bigDifferencePoints.append((common_L[i], gv, percentDifference))

    def plot(self):
        plt.figure()
        for var in self.vars:
            if var in self.includedVars:
                gcolor = self.gotamaVarColorPairs.get(var)
                lcolor = self.glarborgVarColorPairs.get(var)
                plt.plot(self.x_axisL_gotama, self.gotama_data.get_variable(var), '.-',
                          label=f"{var} (Gotama)", color=gcolor)
                plt.plot(self.x_axisL_glarborg, self.glarborg_data.get_variable(var), '.-',
                          label=f"{var} (Glarborg)", color=lcolor)

        # hot spots#"{num:.2f}
        #for bigDifferencePoint in self.bigDifferencePoints:
        #    plt.scatter(bigDifferencePoint[0], bigDifferencePoint[1], color='black', marker='x', zorder=5, label=f'% difference of: {bigDifferencePoint[2]}, at L={bigDifferencePoint[0]},{bigDifferencePoint[1]}')
        #plt.scatter(self.maxValueDifferencePoint[0], self.maxValueDifferencePoint[1], color='black', marker='o', zorder=7, label=f'MAX value difference of: {self.maxValueDifferencePoint[2]:.6f} or {self.maxPercentageDifferencePoint[2]:.6f}%, at L={self.maxValueDifferencePoint[0]:.6f},{self.maxValueDifferencePoint[1]:.6f}')
        #plt.scatter(self.maxPercentageDifferencePoint[0], self.maxPercentageDifferencePoint[1], color='black', marker='o', zorder=7, label=f'MAX % difference of: {self.maxPercentageDifferencePoint[2]},  at L={self.maxPercentageDifferencePoint[0]},{self.maxPercentageDifferencePoint[1]}')

        plt.xlabel('L')
        plt.ylabel('Measured Variables')
        plt.title(self.title)
        plt.legend()

class Pdrlet_plotter():
    def __init__(self, pdrlet_file):
        self.pdrlet_file = pdrlet_file
        self.pdrlet_data = pdf.pdrs_data_file(pdrlet_file)

        self.title = pdrlet_file.split("/")[-1].split(".")[0] # this just takes the file name without the directory or extension for the title of the plot

        self.vars = self.pdrlet_data.datavars
        self.x_axisL = self.pdrlet_data.get_axis('L')

        self.excludedVars = ["Chi_LL[1/s]", "mdotL/rho[1/s]", "ProdRateYR[kg/m^3s]", "density[kg/m^3]", "molarmass[kg/mol]", "lambda[W/m K]", "cp[J/kg K]", "mu[kg/sm]"]
        self.includedVars = ["Y-OH", "Y-NO2", "Y-NO", "Y-H2", "Y-N2O", "Y-NH3"] #, "T[K]"]
        self.colorOrder = ['red', 'orange', 'green', 'darkblue', 'royalblue', 'slategray', "gold"]

        self.varColorPairs = {}
        for i,var in enumerate(self.includedVars):
            if (i < len(self.colorOrder)):
                self.varColorPairs[var] = self.colorOrder[i]

    def plot(self):
        plt.figure()
        for i,var in enumerate(self.vars):
            if var in self.includedVars: #i != 1 and i != 0 and not (var in self.excludedVars):#
                if var in self.varColorPairs.keys():
                    plt.plot(self.x_axisL, self.pdrlet_data.get_variable(var), '.-', label=var, color=self.varColorPairs[var])
                else: plt.plot(self.x_axisL, self.pdrlet_data.get_variable(var), '.-', label=var)

        plt.xlabel('L')
        plt.ylabel('Measured Variables')
        plt.title(self.title)

        plt.legend()


comparison_files = ["output/Glarborg/NH3/NH3_GlarborgAtm_E0-7.Y", "output/Glarborg/NH3/NH3_GlarborgAtm_E1-0.Y", "output/Glarborg/NH3/NH3_GlarborgAtm_E1-4.Y",
                   "output/Gotama/NH3/NH3_GotamaAtm_E0-7.Y", "output/Gotama/NH3/NH3_GotamaAtm_E1-0.Y", "output/Gotama/NH3/NH3_GotamaAtm_E1-4.Y",
                   "output/Glarborg/NH3/NH3_GlarborgTurbine_E0-7.Y", "output/Glarborg/NH3/NH3_GlarborgTurbine_E1-0.Y", "output/Glarborg/NH3/NH3_GlarborgTurbine_E1-4.Y",
                   "output/Gotama/NH3/NH3_GotamaTurbine_E0-7.Y", "output/Gotama/NH3/NH3_GotamaTurbine_E1-0.Y", "output/Gotama/NH3/NH3_GotamaTurbine_E1-4.Y",
                    "output/Glarborg/NH3/NH3_GlarborgColdTurbine_E0-7.Y", "output/Glarborg/NH3/NH3_GlarborgColdTurbine_E1-0.Y", "output/Glarborg/NH3/NH3_GlarborgColdTurbine_E1-4.Y",
                   "output/Gotama/NH3/NH3_GotamaColdTurbine_E0-7.Y", "output/Gotama/NH3/NH3_GotamaColdTurbine_E1-0.Y", "output/Gotama/NH3/NH3_GotamaColdTurbine_E1-4.Y",

                   "output/Glarborg/Cracked/95-5/Cracked_95-5_GlarborgAtm_E0-7.Y", "output/Glarborg/Cracked/95-5/Cracked_95-5_GlarborgAtm_E1-0.Y", "output/Glarborg/Cracked/95-5/Cracked_95-5_GlarborgAtm_E1-4.Y",
                   "output/Gotama/Cracked/95-5/Cracked_95-5_GotamaAtm_E0-7.Y", "output/Gotama/Cracked/95-5/Cracked_95-5_GotamaAtm_E1-0.Y", "output/Gotama/Cracked/95-5/Cracked_95-5_GotamaAtm_E1-4.Y",
                   "output/Glarborg/Cracked/95-5/Cracked_95-5_GlarborgTurbine_E0-7.Y", "output/Glarborg/Cracked/95-5/Cracked_95-5_GlarborgTurbine_E1-0.Y", "output/Glarborg/Cracked/95-5/Cracked_95-5_GlarborgTurbine_E1-4.Y",
                   "output/Gotama/Cracked/95-5/Cracked_95-5_GotamaTurbine_E0-7.Y", "output/Gotama/Cracked/95-5/Cracked_95-5_GotamaTurbine_E1-0.Y", "output/Gotama/Cracked/95-5/Cracked_95-5_GotamaTurbine_E1-4.Y",
                    "output/Glarborg/Cracked/95-5/Cracked_95-5_GlarborgColdTurbine_E0-7.Y", "output/Glarborg/Cracked/95-5/Cracked_95-5_GlarborgColdTurbine_E1-0.Y", "output/Glarborg/Cracked/95-5/Cracked_95-5_GlarborgColdTurbine_E1-4.Y",
                   "output/Gotama/Cracked/95-5/Cracked_95-5_GotamaColdTurbine_E0-7.Y", "output/Gotama/Cracked/95-5/Cracked_95-5_GotamaColdTurbine_E1-0.Y", "output/Gotama/Cracked/95-5/Cracked_95-5_GotamaColdTurbine_E1-4.Y",
                    
                    "output/Glarborg/Cracked/90-10/Cracked_90-10_GlarborgAtm_E0-7.Y", "output/Glarborg/Cracked/90-10/Cracked_90-10_GlarborgAtm_E1-0.Y", "output/Glarborg/Cracked/90-10/Cracked_90-10_GlarborgAtm_E1-4.Y",
                   "output/Gotama/Cracked/90-10/Cracked_90-10_GotamaAtm_E0-7.Y", "output/Gotama/Cracked/90-10/Cracked_90-10_GotamaAtm_E1-0.Y", "output/Gotama/Cracked/90-10/Cracked_90-10_GotamaAtm_E1-4.Y",
                   "output/Glarborg/Cracked/90-10/Cracked_90-10_GlarborgTurbine_E0-7.Y", "output/Glarborg/Cracked/90-10/Cracked_90-10_GlarborgTurbine_E1-0.Y", "output/Glarborg/Cracked/90-10/Cracked_90-10_GlarborgTurbine_E1-4.Y",
                   "output/Gotama/Cracked/90-10/Cracked_90-10_GotamaTurbine_E0-7.Y", "output/Gotama/Cracked/90-10/Cracked_90-10_GotamaTurbine_E1-0.Y", "output/Gotama/Cracked/90-10/Cracked_90-10_GotamaTurbine_E1-4.Y",
                    "output/Glarborg/Cracked/90-10/Cracked_90-10_GlarborgColdTurbine_E0-7.Y", "output/Glarborg/Cracked/90-10/Cracked_90-10_GlarborgColdTurbine_E1-0.Y", "output/Glarborg/Cracked/90-10/Cracked_90-10_GlarborgColdTurbine_E1-4.Y",
                   "output/Gotama/Cracked/90-10/Cracked_90-10_GotamaColdTurbine_E0-7.Y", "output/Gotama/Cracked/90-10/Cracked_90-10_GotamaColdTurbine_E1-0.Y", "output/Gotama/Cracked/90-10/Cracked_90-10_GotamaColdTurbine_E1-4.Y",

                   "output/Glarborg/Cracked/85-15/Cracked_85-15_GlarborgAtm_E0-7.Y", "output/Glarborg/Cracked/85-15/Cracked_85-15_GlarborgAtm_E1-0.Y", "output/Glarborg/Cracked/85-15/Cracked_85-15_GlarborgAtm_E1-4.Y",
                   "output/Gotama/Cracked/85-15/Cracked_85-15_GotamaAtm_E0-7.Y", "output/Gotama/Cracked/85-15/Cracked_85-15_GotamaAtm_E1-0.Y", "output/Gotama/Cracked/85-15/Cracked_85-15_GotamaAtm_E1-4.Y",
                   "output/Glarborg/Cracked/85-15/Cracked_85-15_GlarborgTurbine_E0-7.Y", "output/Glarborg/Cracked/85-15/Cracked_85-15_GlarborgTurbine_E1-0.Y", "output/Glarborg/Cracked/85-15/Cracked_85-15_GlarborgTurbine_E1-4.Y",
                   "output/Gotama/Cracked/85-15/Cracked_85-15_GotamaTurbine_E0-7.Y", "output/Gotama/Cracked/85-15/Cracked_85-15_GotamaTurbine_E1-0.Y", "output/Gotama/Cracked/85-15/Cracked_85-15_GotamaTurbine_E1-4.Y",
                    "output/Glarborg/Cracked/85-15/Cracked_85-15_GlarborgColdTurbine_E0-7.Y", "output/Glarborg/Cracked/85-15/Cracked_85-15_GlarborgColdTurbine_E1-0.Y", "output/Glarborg/Cracked/85-15/Cracked_85-15_GlarborgColdTurbine_E1-4.Y",
                   "output/Gotama/Cracked/85-15/Cracked_85-15_GotamaColdTurbine_E0-7.Y", "output/Gotama/Cracked/85-15/Cracked_85-15_GotamaColdTurbine_E1-0.Y", "output/Gotama/Cracked/85-15/Cracked_85-15_GotamaColdTurbine_E1-4.Y",
                   
                   "output/Glarborg/Cracked/80-20/Cracked_80-20_GlarborgAtm_E0-7.Y", "output/Glarborg/Cracked/80-20/Cracked_80-20_GlarborgAtm_E1-0.Y", "output/Glarborg/Cracked/80-20/Cracked_80-20_GlarborgAtm_E1-4.Y",
                   "output/Gotama/Cracked/80-20/Cracked_80-20_GotamaAtm_E0-7.Y", "output/Gotama/Cracked/80-20/Cracked_80-20_GotamaAtm_E1-0.Y", "output/Gotama/Cracked/80-20/Cracked_80-20_GotamaAtm_E1-4.Y",
                   "output/Glarborg/Cracked/80-20/Cracked_80-20_GlarborgTurbine_E0-7.Y", "output/Glarborg/Cracked/80-20/Cracked_80-20_GlarborgTurbine_E1-0.Y", "output/Glarborg/Cracked/80-20/Cracked_80-20_GlarborgTurbine_E1-4.Y",
                   "output/Gotama/Cracked/80-20/Cracked_80-20_GotamaTurbine_E0-7.Y", "output/Gotama/Cracked/80-20/Cracked_80-20_GotamaTurbine_E1-0.Y", "output/Gotama/Cracked/80-20/Cracked_80-20_GotamaTurbine_E1-4.Y",
                    "output/Glarborg/Cracked/80-20/Cracked_80-20_GlarborgColdTurbine_E0-7.Y", "output/Glarborg/Cracked/80-20/Cracked_80-20_GlarborgColdTurbine_E1-0.Y", "output/Glarborg/Cracked/80-20/Cracked_80-20_GlarborgColdTurbine_E1-4.Y",
                   "output/Gotama/Cracked/80-20/Cracked_80-20_GotamaColdTurbine_E0-7.Y", "output/Gotama/Cracked/80-20/Cracked_80-20_GotamaColdTurbine_E1-0.Y", "output/Gotama/Cracked/80-20/Cracked_80-20_GotamaColdTurbine_E1-4.Y",
                   
                   "output/Glarborg/Cracked/40-60/Cracked_40-60_GlarborgAtm_E0-7.Y", "output/Glarborg/Cracked/40-60/Cracked_40-60_GlarborgAtm_E1-0.Y", "output/Glarborg/Cracked/40-60/Cracked_40-60_GlarborgAtm_E1-4.Y",
                   "output/Gotama/Cracked/40-60/Cracked_40-60_GotamaAtm_E0-7.Y", "output/Gotama/Cracked/40-60/Cracked_40-60_GotamaAtm_E1-0.Y", "output/Gotama/Cracked/40-60/Cracked_40-60_GotamaAtm_E1-4.Y",
                   "output/Glarborg/Cracked/40-60/Cracked_40-60_GlarborgTurbine_E0-7.Y", "output/Glarborg/Cracked/40-60/Cracked_40-60_GlarborgTurbine_E1-0.Y", "output/Glarborg/Cracked/40-60/Cracked_40-60_GlarborgTurbine_E1-4.Y",
                   "output/Gotama/Cracked/40-60/Cracked_40-60_GotamaTurbine_E0-7.Y", "output/Gotama/Cracked/40-60/Cracked_40-60_GotamaTurbine_E1-0.Y", "output/Gotama/Cracked/40-60/Cracked_40-60_GotamaTurbine_E1-4.Y",
                    "output/Glarborg/Cracked/40-60/Cracked_40-60_GlarborgColdTurbine_E0-7.Y", "output/Glarborg/Cracked/40-60/Cracked_40-60_GlarborgColdTurbine_E1-0.Y", "output/Glarborg/Cracked/40-60/Cracked_40-60_GlarborgColdTurbine_E1-4.Y",
                   "output/Gotama/Cracked/40-60/Cracked_40-60_GotamaColdTurbine_E0-7.Y", "output/Gotama/Cracked/40-60/Cracked_40-60_GotamaColdTurbine_E1-0.Y", "output/Gotama/Cracked/40-60/Cracked_40-60_GotamaColdTurbine_E1-4.Y",
                   
                   "output/Glarborg/Cracked/20-80/Cracked_20-80_GlarborgAtm_E0-7.Y", "output/Glarborg/Cracked/20-80/Cracked_20-80_GlarborgAtm_E1-0.Y", "output/Glarborg/Cracked/20-80/Cracked_20-80_GlarborgAtm_E1-4.Y",
                   "output/Gotama/Cracked/20-80/Cracked_20-80_GotamaAtm_E0-7.Y", "output/Gotama/Cracked/20-80/Cracked_20-80_GotamaAtm_E1-0.Y", "output/Gotama/Cracked/20-80/Cracked_20-80_GotamaAtm_E1-4.Y",
                   "output/Glarborg/Cracked/20-80/Cracked_20-80_GlarborgTurbine_E0-7.Y", "output/Glarborg/Cracked/20-80/Cracked_20-80_GlarborgTurbine_E1-0.Y", "output/Glarborg/Cracked/20-80/Cracked_20-80_GlarborgTurbine_E1-4.Y",
                   "output/Gotama/Cracked/20-80/Cracked_20-80_GotamaTurbine_E0-7.Y", "output/Gotama/Cracked/20-80/Cracked_20-80_GotamaTurbine_E1-0.Y", "output/Gotama/Cracked/20-80/Cracked_20-80_GotamaTurbine_E1-4.Y",
                    "output/Glarborg/Cracked/20-80/Cracked_20-80_GlarborgColdTurbine_E0-7.Y", "output/Glarborg/Cracked/20-80/Cracked_20-80_GlarborgColdTurbine_E1-0.Y", "output/Glarborg/Cracked/20-80/Cracked_20-80_GlarborgColdTurbine_E1-4.Y",
                   "output/Gotama/Cracked/20-80/Cracked_20-80_GotamaColdTurbine_E0-7.Y", "output/Gotama/Cracked/20-80/Cracked_20-80_GotamaColdTurbine_E1-0.Y", "output/Gotama/Cracked/20-80/Cracked_20-80_GotamaColdTurbine_E1-4.Y",
                   
                   "output/Glarborg/Cracked/10-90/Cracked_10-90_GlarborgAtm_E0-7.Y", "output/Glarborg/Cracked/10-90/Cracked_10-90_GlarborgAtm_E1-0.Y", "output/Glarborg/Cracked/10-90/Cracked_10-90_GlarborgAtm_E1-4.Y",
                   "output/Gotama/Cracked/10-90/Cracked_10-90_GotamaAtm_E0-7.Y", "output/Gotama/Cracked/10-90/Cracked_10-90_GotamaAtm_E1-0.Y", "output/Gotama/Cracked/10-90/Cracked_10-90_GotamaAtm_E1-4.Y",
                   "output/Glarborg/Cracked/10-90/Cracked_10-90_GlarborgTurbine_E0-7.Y", "output/Glarborg/Cracked/10-90/Cracked_10-90_GlarborgTurbine_E1-0.Y", "output/Glarborg/Cracked/10-90/Cracked_10-90_GlarborgTurbine_E1-4.Y",
                   "output/Gotama/Cracked/10-90/Cracked_10-90_GotamaTurbine_E0-7.Y", "output/Gotama/Cracked/10-90/Cracked_10-90_GotamaTurbine_E1-0.Y", "output/Gotama/Cracked/10-90/Cracked_10-90_GotamaTurbine_E1-4.Y",
                    "output/Glarborg/Cracked/10-90/Cracked_10-90_GlarborgColdTurbine_E0-7.Y", "output/Glarborg/Cracked/10-90/Cracked_10-90_GlarborgColdTurbine_E1-0.Y", "output/Glarborg/Cracked/10-90/Cracked_10-90_GlarborgColdTurbine_E1-4.Y",
                   "output/Gotama/Cracked/10-90/Cracked_10-90_GotamaColdTurbine_E0-7.Y", "output/Gotama/Cracked/10-90/Cracked_10-90_GotamaColdTurbine_E1-0.Y", "output/Gotama/Cracked/10-90/Cracked_10-90_GotamaColdTurbine_E1-4.Y",
                   
                   "output/Glarborg/Cracked/5-95/Cracked_5-95_GlarborgAtm_E0-7.Y", "output/Glarborg/Cracked/5-95/Cracked_5-95_GlarborgAtm_E1-0.Y", "output/Glarborg/Cracked/5-95/Cracked_5-95_GlarborgAtm_E1-4.Y",
                   "output/Gotama/Cracked/5-95/Cracked_5-95_GotamaAtm_E0-7.Y", "output/Gotama/Cracked/5-95/Cracked_5-95_GotamaAtm_E1-0.Y", "output/Gotama/Cracked/5-95/Cracked_5-95_GotamaAtm_E1-4.Y",
                   "output/Glarborg/Cracked/5-95/Cracked_5-95_GlarborgTurbine_E0-7.Y", "output/Glarborg/Cracked/5-95/Cracked_5-95_GlarborgTurbine_E1-0.Y", "output/Glarborg/Cracked/5-95/Cracked_5-95_GlarborgTurbine_E1-4.Y",
                   "output/Gotama/Cracked/5-95/Cracked_5-95_GotamaTurbine_E0-7.Y", "output/Gotama/Cracked/5-95/Cracked_5-95_GotamaTurbine_E1-0.Y", "output/Gotama/Cracked/5-95/Cracked_5-95_GotamaTurbine_E1-4.Y",
                    "output/Glarborg/Cracked/5-95/Cracked_5-95_GlarborgColdTurbine_E0-7.Y", "output/Glarborg/Cracked/5-95/Cracked_5-95_GlarborgColdTurbine_E1-0.Y", "output/Glarborg/Cracked/5-95/Cracked_5-95_GlarborgColdTurbine_E1-4.Y",
                   "output/Gotama/Cracked/5-95/Cracked_5-95_GotamaColdTurbine_E0-7.Y", "output/Gotama/Cracked/5-95/Cracked_5-95_GotamaColdTurbine_E1-0.Y", "output/Gotama/Cracked/5-95/Cracked_5-95_GotamaColdTurbine_E1-4.Y",
                   
                   "output/Glarborg/Cracked/1-99/Cracked_1-99_GlarborgAtm_E0-7.Y", "output/Glarborg/Cracked/1-99/Cracked_1-99_GlarborgAtm_E1-0.Y", "output/Glarborg/Cracked/1-99/Cracked_1-99_GlarborgAtm_E1-4.Y",
                   "output/Gotama/Cracked/1-99/Cracked_1-99_GotamaAtm_E0-7.Y", "output/Gotama/Cracked/1-99/Cracked_1-99_GotamaAtm_E1-0.Y", "output/Gotama/Cracked/1-99/Cracked_1-99_GotamaAtm_E1-4.Y",
                   "output/Glarborg/Cracked/1-99/Cracked_1-99_GlarborgTurbine_E0-7.Y", "output/Glarborg/Cracked/1-99/Cracked_1-99_GlarborgTurbine_E1-0.Y", "output/Glarborg/Cracked/1-99/Cracked_1-99_GlarborgTurbine_E1-4.Y",
                   "output/Gotama/Cracked/1-99/Cracked_1-99_GotamaTurbine_E0-7.Y", "output/Gotama/Cracked/1-99/Cracked_1-99_GotamaTurbine_E1-0.Y", "output/Gotama/Cracked/1-99/Cracked_1-99_GotamaTurbine_E1-4.Y",
                    "output/Glarborg/Cracked/1-99/Cracked_1-99_GlarborgColdTurbine_E0-7.Y", "output/Glarborg/Cracked/1-99/Cracked_1-99_GlarborgColdTurbine_E1-0.Y", "output/Glarborg/Cracked/1-99/Cracked_1-99_GlarborgColdTurbine_E1-4.Y",
                   "output/Gotama/Cracked/1-99/Cracked_1-99_GotamaColdTurbine_E0-7.Y", "output/Gotama/Cracked/1-99/Cracked_1-99_GotamaColdTurbine_E1-0.Y", "output/Gotama/Cracked/1-99/Cracked_1-99_GotamaColdTurbine_E1-4.Y",
                   
                   "output/Glarborg/H2/H2_GlarborgAtm_E0-7.Y", "output/Glarborg/H2/H2_GlarborgAtm_E1-0.Y", "output/Glarborg/H2/H2_GlarborgAtm_E1-4.Y",
                   "output/Gotama/H2/H2_GotamaAtm_E0-7.Y", "output/Gotama/H2/H2_GotamaAtm_E1-0.Y", "output/Gotama/H2/H2_GotamaAtm_E1-4.Y",
                   "output/Glarborg/H2/H2_GlarborgTurbine_E0-7.Y", "output/Glarborg/H2/H2_GlarborgTurbine_E1-0.Y", "output/Glarborg/H2/H2_GlarborgTurbine_E1-4.Y",
                   "output/Gotama/H2/H2_GotamaTurbine_E0-7.Y", "output/Gotama/H2/H2_GotamaTurbine_E1-0.Y", "output/Gotama/H2/H2_GotamaTurbine_E1-4.Y",
                    "output/Glarborg/H2/H2_GlarborgColdTurbine_E0-7.Y", "output/Glarborg/H2/H2_GlarborgColdTurbine_E1-0.Y", "output/Glarborg/H2/H2_GlarborgColdTurbine_E1-4.Y",
                   "output/Gotama/H2/H2_GotamaColdTurbine_E0-7.Y", "output/Gotama/H2/H2_GotamaColdTurbine_E1-0.Y", "output/Gotama/H2/H2_GotamaColdTurbine_E1-4.Y"]
# data = {'Mol': ["Y-OH", "Y-NO2", "Y-NO", "Y-H2", "Y-N2O", "Y-NH3"],
#         'Atm': {'Gotama Max': [[], [], []], 'Glarborg Max': [[], [], []], 'Diff': [[], [], []], '%Diff': [[], [], []]},
#         'Turb': {'Gotama Max': [[], [], []], 'Glarborg Max': [[], [], []], 'Diff': [[], [], []], '%Diff': [[], [], []]},
#         'Cold': {'Gotama Max': [[], [], []], 'Glarborg Max': [[], [], []], 'Diff': [[], [], []], '%Diff': [[], [], []]}}
# Mol                                   Turbine                                                                     Atmospheric and then.. .Cold
#        E0-7, E1-0, E1-4           E0-7, E1-0, E1-4             E0-7, E1-0, E1-4              E0-7, E1-0, E1-4
#        Gotama Max Value           Glarborg Max Value           Difference (Got-Glar)         % Difference
#Y-OH
#Y-N2
#Y-N2O

# start = 24
# end = 36

# steps = 3
# stepCount = 0
# for i,file in enumerate(comparison_files):
#     if (i>=start and i<end):
#         if stepCount < 3:
#             plotter = MultiPlotter(file, comparison_files[i+3])
#             plotter.plot()
#             #plt.savefig(f"images/{plotter.title}.png")
#         stepCount += 1
#         if stepCount == 6: stepCount = 0
        

# plt.show()

new_comparison_files =["output/Gotama/Cracked/70-30/Cracked_70-30_GotamaAtm_E0-7_Lewis.Y", "output/Gotama/Cracked/70-30/Cracked_70-30_GotamaAtm_E0-7.Y",
                       "output/Gotama/Cracked/70-30/Cracked_70-30_GotamaAtm_E1-0_Lewis.Y", "output/Gotama/Cracked/70-30/Cracked_70-30_GotamaAtm_E1-0.Y",
                       "output/Gotama/Cracked/70-30/Cracked_70-30_GotamaAtm_E1-4_Lewis.Y", "output/Gotama/Cracked/70-30/Cracked_70-30_GotamaAtm_E1-4.Y",
                       "output/Gotama/Cracked/20-80/Cracked_20-80_GotamaAtm_E0-7_Lewis.Y", "output/Gotama/Cracked/20-80/Cracked_20-80_GotamaAtm_E0-7.Y"]
                        #"output/Gotama/Cracked/40-60/Cracked_40-60_GotamaTurbine_E0-7_Lewis.Y", "output/Gotama/Cracked/40-60/Cracked_40-60_GotamaTurbine_E0-7.Y"]
# for i,files in enumerate(new_comparison_files):
#     plotter = MultiPlotter(files[0], files[1])
#     plotter.plot()
    #plt.savefig(f"images/{plotter.title}.png")
for i,file in enumerate(comparison_files):
    for j in range(2):
        if j == 1:
            file = file.split(".")[0] + "_Lewis.Y"
            
        plotter = Pdrlet_plotter(file)
        plotter.plot()
        plt.savefig(f"images/{plotter.title}.png")

plt.show()