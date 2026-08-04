import subprocess
import os

def runPdrs(file_path, pdrsType=1):
    if pdrsType == 1:
        print("-------------------------using regular pdrs-------------------------")
        os.system(f"pdrs {file_path}")
    elif pdrsType == 2:
        print("-------------------------Using PDRS-str!-------------------------")
        os.system(f"~/PDRS-str/bin/pdrs {file_path}")
