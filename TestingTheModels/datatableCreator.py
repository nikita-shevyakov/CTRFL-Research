import pandas as pd
import numpy as np
import pdrs_data_file as pdf
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt

def save_pretty_html(df, filename="lewis_nums.html"):

    html = df.to_html(
        sparsify=True,
        border=0,
        classes="lewis-table",
        table_id="lewis"
    )

    css = """
<style>

body{
    font-family:Arial,Helvetica,sans-serif;
    margin:20px;
}


/* ---------- TABLE ---------- */

table.lewis-table{
    border-collapse:collapse;
    font-size:11px;
}

table.lewis-table td,
table.lewis-table th{
    border:1px solid #c7c7c7;
    padding:4px 6px;
    text-align:center;
}


/* ---------- FUEL HEADER ---------- */

thead tr:nth-child(1) th{
    background:#333333;
    color:white;
    font-size:13px;
}


/* ---------- CONDITION HEADER COLORS ---------- */

.atm{
    background:#8fd18f !important;
    color:black;
}

.turb{
    background:#ffc87a !important;
    color:black;
}

.cold{
    background:#99c9ff !important;
    color:black;
}


/* ---------- EQUIVALENCE RATIO COLORS ---------- */

.e07{
    background:#dff0ff;
}

.e10{
    background:#b8dcff;
}

.e14{
    background:#8fc4ff;
}


/* ---------- NORM / LEWIS ---------- */

.norm{
    border-left:2px solid #777;
}

.lew{
    font-weight:bold;
    border-right:2px solid #777;
}


/* ---------- ROW HEADERS ---------- */

tbody th{
    background:#404040;
    color:white;
    font-weight:bold;
}


/* ---------- HOVER ---------- */

tbody tr:hover td{
    background:#fff6b0 !important;
}


/* ---------- STICKY HEADERS ---------- */

thead th{
    position:sticky;
    top:0;
    z-index:2;
}

tbody th{
    position:sticky;
    left:0;
    z-index:1;
}

thead tr:first-child th:first-child{
    z-index:3;
}

</style>
"""


    # ----------------------------------------------------------
    # Add CSS classes based on dataframe columns
    # ----------------------------------------------------------

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table")
    rows = table.find_all("tr")

    # number of row index columns
    index_cols = len(df.index.names)


    for col_index, col in enumerate(df.columns):

        eq_ratio = col[2]
        spec = col[3]

        classes = []

        if eq_ratio == "E0.7":
            classes.append("e07")

        elif eq_ratio == "E1.0":
            classes.append("e10")

        elif eq_ratio == "E1.4":
            classes.append("e14")


        if spec == "Norm":
            classes.append("norm")

        # elif spec == "Lew":
        #     classes.append("lew")
        elif spec == "HiDis":
            classes.append("lew")


        html_col = col_index


        for row in rows:

            cells = row.find_all("td")

            if html_col < len(cells):

                cells[html_col]["class"] = (
                    cells[html_col].get("class", []) + classes
                )



    # ----------------------------------------------------------
    # Color condition headers
    # ----------------------------------------------------------

    for cell in soup.find_all(["th","td"]):

        text = cell.text.strip()

        if text == "Atm":
            cell["class"] = cell.get("class", []) + ["atm"]

        elif text == "Turb":
            cell["class"] = cell.get("class", []) + ["turb"]

        elif text == "Cold":
            cell["class"] = cell.get("class", []) + ["cold"]



    # ----------------------------------------------------------
    # Save HTML
    # ----------------------------------------------------------

    with open(filename, "w") as f:
        f.write(css)
        f.write(str(soup))

def calcMetrics(gotamaFile, glarborgFile, molecules):
    """
    return dictionary of form {"Y-OH":[Got Max, Glar max, Diff, %diff], "Y-__":[]}
    """
    threshhold = 1e-7
    gotama_data = pdf.pdrs_data_file(gotamaFile)
    glarborg_data = pdf.pdrs_data_file(glarborgFile)

    returnDict = {}
    
    for molecule in molecules:
        maxGotamaVal = np.max(gotama_data.get_variable(molecule))
        maxGlarborgVal = np.max(glarborg_data.get_variable(molecule))

        diff = maxGotamaVal - maxGlarborgVal
        if (abs(maxGotamaVal) + abs(maxGlarborgVal)) / 2 > threshhold:
            percentDiff = (maxGotamaVal - maxGlarborgVal) / ((abs(maxGotamaVal) + abs(maxGlarborgVal)) / 2) * 100
            returnDict[molecule] = [maxGotamaVal, maxGlarborgVal, diff, percentDiff]

    return returnDict



comparison_files = [[["output/Glarborg/NH3/NH3_GlarborgAtm_E0-7.Y", "output/Glarborg/NH3/NH3_GlarborgAtm_E1-0.Y", "output/Glarborg/NH3/NH3_GlarborgAtm_E1-4.Y",
                   "output/Gotama/NH3/NH3_GotamaAtm_E0-7.Y", "output/Gotama/NH3/NH3_GotamaAtm_E1-0.Y", "output/Gotama/NH3/NH3_GotamaAtm_E1-4.Y"],
                   ["output/Glarborg/NH3/NH3_GlarborgTurbine_E0-7.Y", "output/Glarborg/NH3/NH3_GlarborgTurbine_E1-0.Y", "output/Glarborg/NH3/NH3_GlarborgTurbine_E1-4.Y",
                   "output/Gotama/NH3/NH3_GotamaTurbine_E0-7.Y", "output/Gotama/NH3/NH3_GotamaTurbine_E1-0.Y", "output/Gotama/NH3/NH3_GotamaTurbine_E1-4.Y"],
                    ["output/Glarborg/NH3/NH3_GlarborgColdTurbine_E0-7.Y", "output/Glarborg/NH3/NH3_GlarborgColdTurbine_E1-0.Y", "output/Glarborg/NH3/NH3_GlarborgColdTurbine_E1-4.Y",
                   "output/Gotama/NH3/NH3_GotamaColdTurbine_E0-7.Y", "output/Gotama/NH3/NH3_GotamaColdTurbine_E1-0.Y", "output/Gotama/NH3/NH3_GotamaColdTurbine_E1-4.Y"]],

                   [["output/Glarborg/Cracked/95-5/Cracked_95-5_GlarborgAtm_E0-7.Y", "output/Glarborg/Cracked/95-5/Cracked_95-5_GlarborgAtm_E1-0.Y", "output/Glarborg/Cracked/95-5/Cracked_95-5_GlarborgAtm_E1-4.Y",
                   "output/Gotama/Cracked/95-5/Cracked_95-5_GotamaAtm_E0-7.Y", "output/Gotama/Cracked/95-5/Cracked_95-5_GotamaAtm_E1-0.Y", "output/Gotama/Cracked/95-5/Cracked_95-5_GotamaAtm_E1-4.Y"],
                   ["output/Glarborg/Cracked/95-5/Cracked_95-5_GlarborgTurbine_E0-7.Y", "output/Glarborg/Cracked/95-5/Cracked_95-5_GlarborgTurbine_E1-0.Y", "output/Glarborg/Cracked/95-5/Cracked_95-5_GlarborgTurbine_E1-4.Y",
                   "output/Gotama/Cracked/95-5/Cracked_95-5_GotamaTurbine_E0-7.Y", "output/Gotama/Cracked/95-5/Cracked_95-5_GotamaTurbine_E1-0.Y", "output/Gotama/Cracked/95-5/Cracked_95-5_GotamaTurbine_E1-4.Y"],
                    ["output/Glarborg/Cracked/95-5/Cracked_95-5_GlarborgColdTurbine_E0-7.Y", "output/Glarborg/Cracked/95-5/Cracked_95-5_GlarborgColdTurbine_E1-0.Y", "output/Glarborg/Cracked/95-5/Cracked_95-5_GlarborgColdTurbine_E1-4.Y",
                   "output/Gotama/Cracked/95-5/Cracked_95-5_GotamaColdTurbine_E0-7.Y", "output/Gotama/Cracked/95-5/Cracked_95-5_GotamaColdTurbine_E1-0.Y", "output/Gotama/Cracked/95-5/Cracked_95-5_GotamaColdTurbine_E1-4.Y"]],
                    
                    [["output/Glarborg/Cracked/90-10/Cracked_90-10_GlarborgAtm_E0-7.Y", "output/Glarborg/Cracked/90-10/Cracked_90-10_GlarborgAtm_E1-0.Y", "output/Glarborg/Cracked/90-10/Cracked_90-10_GlarborgAtm_E1-4.Y",
                   "output/Gotama/Cracked/90-10/Cracked_90-10_GotamaAtm_E0-7.Y", "output/Gotama/Cracked/90-10/Cracked_90-10_GotamaAtm_E1-0.Y", "output/Gotama/Cracked/90-10/Cracked_90-10_GotamaAtm_E1-4.Y"],
                   ["output/Glarborg/Cracked/90-10/Cracked_90-10_GlarborgTurbine_E0-7.Y", "output/Glarborg/Cracked/90-10/Cracked_90-10_GlarborgTurbine_E1-0.Y", "output/Glarborg/Cracked/90-10/Cracked_90-10_GlarborgTurbine_E1-4.Y",
                   "output/Gotama/Cracked/90-10/Cracked_90-10_GotamaTurbine_E0-7.Y", "output/Gotama/Cracked/90-10/Cracked_90-10_GotamaTurbine_E1-0.Y", "output/Gotama/Cracked/90-10/Cracked_90-10_GotamaTurbine_E1-4.Y"],
                    ["output/Glarborg/Cracked/90-10/Cracked_90-10_GlarborgColdTurbine_E0-7.Y", "output/Glarborg/Cracked/90-10/Cracked_90-10_GlarborgColdTurbine_E1-0.Y", "output/Glarborg/Cracked/90-10/Cracked_90-10_GlarborgColdTurbine_E1-4.Y",
                   "output/Gotama/Cracked/90-10/Cracked_90-10_GotamaColdTurbine_E0-7.Y", "output/Gotama/Cracked/90-10/Cracked_90-10_GotamaColdTurbine_E1-0.Y", "output/Gotama/Cracked/90-10/Cracked_90-10_GotamaColdTurbine_E1-4.Y"]],

                   [["output/Glarborg/Cracked/85-15/Cracked_85-15_GlarborgAtm_E0-7.Y", "output/Glarborg/Cracked/85-15/Cracked_85-15_GlarborgAtm_E1-0.Y", "output/Glarborg/Cracked/85-15/Cracked_85-15_GlarborgAtm_E1-4.Y",
                   "output/Gotama/Cracked/85-15/Cracked_85-15_GotamaAtm_E0-7.Y", "output/Gotama/Cracked/85-15/Cracked_85-15_GotamaAtm_E1-0.Y", "output/Gotama/Cracked/85-15/Cracked_85-15_GotamaAtm_E1-4.Y"],
                   ["output/Glarborg/Cracked/85-15/Cracked_85-15_GlarborgTurbine_E0-7.Y", "output/Glarborg/Cracked/85-15/Cracked_85-15_GlarborgTurbine_E1-0.Y", "output/Glarborg/Cracked/85-15/Cracked_85-15_GlarborgTurbine_E1-4.Y",
                   "output/Gotama/Cracked/85-15/Cracked_85-15_GotamaTurbine_E0-7.Y", "output/Gotama/Cracked/85-15/Cracked_85-15_GotamaTurbine_E1-0.Y", "output/Gotama/Cracked/85-15/Cracked_85-15_GotamaTurbine_E1-4.Y"],
                    ["output/Glarborg/Cracked/85-15/Cracked_85-15_GlarborgColdTurbine_E0-7.Y", "output/Glarborg/Cracked/85-15/Cracked_85-15_GlarborgColdTurbine_E1-0.Y", "output/Glarborg/Cracked/85-15/Cracked_85-15_GlarborgColdTurbine_E1-4.Y",
                   "output/Gotama/Cracked/85-15/Cracked_85-15_GotamaColdTurbine_E0-7.Y", "output/Gotama/Cracked/85-15/Cracked_85-15_GotamaColdTurbine_E1-0.Y", "output/Gotama/Cracked/85-15/Cracked_85-15_GotamaColdTurbine_E1-4.Y"]],
                   
                   [["output/Glarborg/Cracked/80-20/Cracked_80-20_GlarborgAtm_E0-7.Y", "output/Glarborg/Cracked/80-20/Cracked_80-20_GlarborgAtm_E1-0.Y", "output/Glarborg/Cracked/80-20/Cracked_80-20_GlarborgAtm_E1-4.Y",
                   "output/Gotama/Cracked/80-20/Cracked_80-20_GotamaAtm_E0-7.Y", "output/Gotama/Cracked/80-20/Cracked_80-20_GotamaAtm_E1-0.Y", "output/Gotama/Cracked/80-20/Cracked_80-20_GotamaAtm_E1-4.Y"],
                   ["output/Glarborg/Cracked/80-20/Cracked_80-20_GlarborgTurbine_E0-7.Y", "output/Glarborg/Cracked/80-20/Cracked_80-20_GlarborgTurbine_E1-0.Y", "output/Glarborg/Cracked/80-20/Cracked_80-20_GlarborgTurbine_E1-4.Y",
                   "output/Gotama/Cracked/80-20/Cracked_80-20_GotamaTurbine_E0-7.Y", "output/Gotama/Cracked/80-20/Cracked_80-20_GotamaTurbine_E1-0.Y", "output/Gotama/Cracked/80-20/Cracked_80-20_GotamaTurbine_E1-4.Y"],
                    ["output/Glarborg/Cracked/80-20/Cracked_80-20_GlarborgColdTurbine_E0-7.Y", "output/Glarborg/Cracked/80-20/Cracked_80-20_GlarborgColdTurbine_E1-0.Y", "output/Glarborg/Cracked/80-20/Cracked_80-20_GlarborgColdTurbine_E1-4.Y",
                   "output/Gotama/Cracked/80-20/Cracked_80-20_GotamaColdTurbine_E0-7.Y", "output/Gotama/Cracked/80-20/Cracked_80-20_GotamaColdTurbine_E1-0.Y", "output/Gotama/Cracked/80-20/Cracked_80-20_GotamaColdTurbine_E1-4.Y"]],
                   
                   [["output/Glarborg/Cracked/40-60/Cracked_40-60_GlarborgAtm_E0-7.Y", "output/Glarborg/Cracked/40-60/Cracked_40-60_GlarborgAtm_E1-0.Y", "output/Glarborg/Cracked/40-60/Cracked_40-60_GlarborgAtm_E1-4.Y",
                   "output/Gotama/Cracked/40-60/Cracked_40-60_GotamaAtm_E0-7.Y", "output/Gotama/Cracked/40-60/Cracked_40-60_GotamaAtm_E1-0.Y", "output/Gotama/Cracked/40-60/Cracked_40-60_GotamaAtm_E1-4.Y"],
                   ["output/Glarborg/Cracked/40-60/Cracked_40-60_GlarborgTurbine_E0-7.Y", "output/Glarborg/Cracked/40-60/Cracked_40-60_GlarborgTurbine_E1-0.Y", "output/Glarborg/Cracked/40-60/Cracked_40-60_GlarborgTurbine_E1-4.Y",
                   "output/Gotama/Cracked/40-60/Cracked_40-60_GotamaTurbine_E0-7.Y", "output/Gotama/Cracked/40-60/Cracked_40-60_GotamaTurbine_E1-0.Y", "output/Gotama/Cracked/40-60/Cracked_40-60_GotamaTurbine_E1-4.Y"],
                    ["output/Glarborg/Cracked/40-60/Cracked_40-60_GlarborgColdTurbine_E0-7.Y", "output/Glarborg/Cracked/40-60/Cracked_40-60_GlarborgColdTurbine_E1-0.Y", "output/Glarborg/Cracked/40-60/Cracked_40-60_GlarborgColdTurbine_E1-4.Y",
                   "output/Gotama/Cracked/40-60/Cracked_40-60_GotamaColdTurbine_E0-7.Y", "output/Gotama/Cracked/40-60/Cracked_40-60_GotamaColdTurbine_E1-0.Y", "output/Gotama/Cracked/40-60/Cracked_40-60_GotamaColdTurbine_E1-4.Y"]],
                   
                   [["output/Glarborg/Cracked/20-80/Cracked_20-80_GlarborgAtm_E0-7.Y", "output/Glarborg/Cracked/20-80/Cracked_20-80_GlarborgAtm_E1-0.Y", "output/Glarborg/Cracked/20-80/Cracked_20-80_GlarborgAtm_E1-4.Y",
                   "output/Gotama/Cracked/20-80/Cracked_20-80_GotamaAtm_E0-7.Y", "output/Gotama/Cracked/20-80/Cracked_20-80_GotamaAtm_E1-0.Y", "output/Gotama/Cracked/20-80/Cracked_20-80_GotamaAtm_E1-4.Y"],
                   ["output/Glarborg/Cracked/20-80/Cracked_20-80_GlarborgTurbine_E0-7.Y", "output/Glarborg/Cracked/20-80/Cracked_20-80_GlarborgTurbine_E1-0.Y", "output/Glarborg/Cracked/20-80/Cracked_20-80_GlarborgTurbine_E1-4.Y",
                   "output/Gotama/Cracked/20-80/Cracked_20-80_GotamaTurbine_E0-7.Y", "output/Gotama/Cracked/20-80/Cracked_20-80_GotamaTurbine_E1-0.Y", "output/Gotama/Cracked/20-80/Cracked_20-80_GotamaTurbine_E1-4.Y"],
                    ["output/Glarborg/Cracked/20-80/Cracked_20-80_GlarborgColdTurbine_E0-7.Y", "output/Glarborg/Cracked/20-80/Cracked_20-80_GlarborgColdTurbine_E1-0.Y", "output/Glarborg/Cracked/20-80/Cracked_20-80_GlarborgColdTurbine_E1-4.Y",
                   "output/Gotama/Cracked/20-80/Cracked_20-80_GotamaColdTurbine_E0-7.Y", "output/Gotama/Cracked/20-80/Cracked_20-80_GotamaColdTurbine_E1-0.Y", "output/Gotama/Cracked/20-80/Cracked_20-80_GotamaColdTurbine_E1-4.Y"]],
                   
                   [["output/Glarborg/Cracked/10-90/Cracked_10-90_GlarborgAtm_E0-7.Y", "output/Glarborg/Cracked/10-90/Cracked_10-90_GlarborgAtm_E1-0.Y", "output/Glarborg/Cracked/10-90/Cracked_10-90_GlarborgAtm_E1-4.Y",
                   "output/Gotama/Cracked/10-90/Cracked_10-90_GotamaAtm_E0-7.Y", "output/Gotama/Cracked/10-90/Cracked_10-90_GotamaAtm_E1-0.Y", "output/Gotama/Cracked/10-90/Cracked_10-90_GotamaAtm_E1-4.Y"],
                   ["output/Glarborg/Cracked/10-90/Cracked_10-90_GlarborgTurbine_E0-7.Y", "output/Glarborg/Cracked/10-90/Cracked_10-90_GlarborgTurbine_E1-0.Y", "output/Glarborg/Cracked/10-90/Cracked_10-90_GlarborgTurbine_E1-4.Y",
                   "output/Gotama/Cracked/10-90/Cracked_10-90_GotamaTurbine_E0-7.Y", "output/Gotama/Cracked/10-90/Cracked_10-90_GotamaTurbine_E1-0.Y", "output/Gotama/Cracked/10-90/Cracked_10-90_GotamaTurbine_E1-4.Y"],
                    ["output/Glarborg/Cracked/10-90/Cracked_10-90_GlarborgColdTurbine_E0-7.Y", "output/Glarborg/Cracked/10-90/Cracked_10-90_GlarborgColdTurbine_E1-0.Y", "output/Glarborg/Cracked/10-90/Cracked_10-90_GlarborgColdTurbine_E1-4.Y",
                   "output/Gotama/Cracked/10-90/Cracked_10-90_GotamaColdTurbine_E0-7.Y", "output/Gotama/Cracked/10-90/Cracked_10-90_GotamaColdTurbine_E1-0.Y", "output/Gotama/Cracked/10-90/Cracked_10-90_GotamaColdTurbine_E1-4.Y"]],
                   
                   [["output/Glarborg/Cracked/5-95/Cracked_5-95_GlarborgAtm_E0-7.Y", "output/Glarborg/Cracked/5-95/Cracked_5-95_GlarborgAtm_E1-0.Y", "output/Glarborg/Cracked/5-95/Cracked_5-95_GlarborgAtm_E1-4.Y",
                   "output/Gotama/Cracked/5-95/Cracked_5-95_GotamaAtm_E0-7.Y", "output/Gotama/Cracked/5-95/Cracked_5-95_GotamaAtm_E1-0.Y", "output/Gotama/Cracked/5-95/Cracked_5-95_GotamaAtm_E1-4.Y"],
                   ["output/Glarborg/Cracked/5-95/Cracked_5-95_GlarborgTurbine_E0-7.Y", "output/Glarborg/Cracked/5-95/Cracked_5-95_GlarborgTurbine_E1-0.Y", "output/Glarborg/Cracked/5-95/Cracked_5-95_GlarborgTurbine_E1-4.Y",
                   "output/Gotama/Cracked/5-95/Cracked_5-95_GotamaTurbine_E0-7.Y", "output/Gotama/Cracked/5-95/Cracked_5-95_GotamaTurbine_E1-0.Y", "output/Gotama/Cracked/5-95/Cracked_5-95_GotamaTurbine_E1-4.Y"],
                    ["output/Glarborg/Cracked/5-95/Cracked_5-95_GlarborgColdTurbine_E0-7.Y", "output/Glarborg/Cracked/5-95/Cracked_5-95_GlarborgColdTurbine_E1-0.Y", "output/Glarborg/Cracked/5-95/Cracked_5-95_GlarborgColdTurbine_E1-4.Y",
                   "output/Gotama/Cracked/5-95/Cracked_5-95_GotamaColdTurbine_E0-7.Y", "output/Gotama/Cracked/5-95/Cracked_5-95_GotamaColdTurbine_E1-0.Y", "output/Gotama/Cracked/5-95/Cracked_5-95_GotamaColdTurbine_E1-4.Y"]],
                   
                #    [["output/Glarborg/Cracked/1-99/Cracked_1-99_GlarborgAtm_E0-7.Y", "output/Glarborg/Cracked/1-99/Cracked_1-99_GlarborgAtm_E1-0.Y", "output/Glarborg/Cracked/1-99/Cracked_1-99_GlarborgAtm_E1-4.Y",
                #    "output/Gotama/Cracked/1-99/Cracked_1-99_GotamaAtm_E0-7.Y", "output/Gotama/Cracked/1-99/Cracked_1-99_GotamaAtm_E1-0.Y", "output/Gotama/Cracked/1-99/Cracked_1-99_GotamaAtm_E1-4.Y"],
                #    ["output/Glarborg/Cracked/1-99/Cracked_1-99_GlarborgTurbine_E0-7.Y", "output/Glarborg/Cracked/1-99/Cracked_1-99_GlarborgTurbine_E1-0.Y", "output/Glarborg/Cracked/1-99/Cracked_1-99_GlarborgTurbine_E1-4.Y",
                #    "output/Gotama/Cracked/1-99/Cracked_1-99_GotamaTurbine_E0-7.Y", "output/Gotama/Cracked/1-99/Cracked_1-99_GotamaTurbine_E1-0.Y", "output/Gotama/Cracked/1-99/Cracked_1-99_GotamaTurbine_E1-4.Y"],
                #     ["output/Glarborg/Cracked/1-99/Cracked_1-99_GlarborgColdTurbine_E0-7.Y", "output/Glarborg/Cracked/1-99/Cracked_1-99_GlarborgColdTurbine_E1-0.Y", "output/Glarborg/Cracked/1-99/Cracked_1-99_GlarborgColdTurbine_E1-4.Y",
                #    "output/Gotama/Cracked/1-99/Cracked_1-99_GotamaColdTurbine_E0-7.Y", "output/Gotama/Cracked/1-99/Cracked_1-99_GotamaColdTurbine_E1-0.Y", "output/Gotama/Cracked/1-99/Cracked_1-99_GotamaColdTurbine_E1-4.Y"]],
                   
                   [["output/Glarborg/H2/H2_GlarborgAtm_E0-7.Y", "output/Glarborg/H2/H2_GlarborgAtm_E1-0.Y", "output/Glarborg/H2/H2_GlarborgAtm_E1-4.Y",
                   "output/Gotama/H2/H2_GotamaAtm_E0-7.Y", "output/Gotama/H2/H2_GotamaAtm_E1-0.Y", "output/Gotama/H2/H2_GotamaAtm_E1-4.Y"],
                   ["output/Glarborg/H2/H2_GlarborgTurbine_E0-7.Y", "output/Glarborg/H2/H2_GlarborgTurbine_E1-0.Y", "output/Glarborg/H2/H2_GlarborgTurbine_E1-4.Y",
                   "output/Gotama/H2/H2_GotamaTurbine_E0-7.Y", "output/Gotama/H2/H2_GotamaTurbine_E1-0.Y", "output/Gotama/H2/H2_GotamaTurbine_E1-4.Y"],
                    ["output/Glarborg/H2/H2_GlarborgColdTurbine_E0-7.Y", "output/Glarborg/H2/H2_GlarborgColdTurbine_E1-0.Y", "output/Glarborg/H2/H2_GlarborgColdTurbine_E1-4.Y",
                   "output/Gotama/H2/H2_GotamaColdTurbine_E0-7.Y", "output/Gotama/H2/H2_GotamaColdTurbine_E1-0.Y", "output/Gotama/H2/H2_GotamaColdTurbine_E1-4.Y"]]]

# CREATE PANDAS DATA TABLE

FUEL = ["NH3", "95-5", "90-10", "85-15", "80-20", "70-30", "60-40", "40-60", "20-80", "10-90", "5-95", "H2"] #"1-99",
CONDITION = ['Atm', "Turb", "Cold"]
#SPECIAL_CONDITION = ["Norm","HiDis"] #"Lew"
METRICS = ["%Diff"]#["Peak Got", "Peak Glar", "Diff", "%Diff"] ##"Diff",
EQR = ["E0.7", "E1.0", "E1.4"]
MOLECULES = ["Y-OH", "Y-NO2", "Y-NO", "Y-N2O"] #, "Y-NH3", "T[K]", "Y-H2"

# columns = pd.MultiIndex.from_product([FUEL, CONDITION, METRICS, EQR, SPECIAL_CONDITION], names = ["Fuel Ratio", "Conditons", "Metrics", "Equi Ratio", "Spec"])

# df = pd.DataFrame(index=pd.Index(MOLECULES, name="Mol"), columns = columns, dtype=float)

columns = pd.MultiIndex.from_product(
    [FUEL, CONDITION, EQR], #, SPECIAL_CONDITION
    names=["Fuel Ratio","Condition","Equi Ratio"] #,"Spec"
)

index = pd.MultiIndex.from_product(
    [MOLECULES, METRICS],
    names=["Molecule","Metric"]
)

df = pd.DataFrame(index=index, columns=columns, dtype=float)


pd.set_option('display.float_format', '{:.1f}'.format)

for num,fuelSet in enumerate(comparison_files):
    fuel = FUEL[num]
    for i,conditionFiles in enumerate(fuelSet):
        condition = "None"
        if i == 0: condition = "Atm"
        elif i == 1: condition = "Turb"
        elif i == 2: condition = "Cold"

        for j in range(int(len(conditionFiles)/2)):
            for iterator in range(1):
                if iterator == 1:
                    glarborgFile = conditionFiles[j].split(".")[0] + "_HiDiss.Y"
                    gotamaFile = conditionFiles[j+3].split(".")[0] + "_HiDiss.Y"
                else:
                    glarborgFile = conditionFiles[j]
                    gotamaFile = conditionFiles[j+3]

                metrics = calcMetrics(gotamaFile, glarborgFile, MOLECULES) # {"Y-OH": [gotMax, glarMax, diff, percentDiff]}

                eqRatio = "0"
                if j == 0: eqRatio = "E0.7"
                elif j == 1: eqRatio = "E1.0"
                elif j == 2: eqRatio = "E1.4"

                special = "Norm"
                if iterator == 1: special = "HiDis" #"Lew"
                for molecule in metrics:
                    # df.loc[(molecule, "Peak Got"),
                    #     (fuel, condition, eqRatio)] = metrics[molecule][0] #, special

                    # df.loc[(molecule, "Peak Glar"),
                    #     (fuel, condition, eqRatio)] = metrics[molecule][1] #, special

                    # df.loc[(molecule, "Diff"),
                    #     (fuel, condition, eqRatio)] = metrics[molecule][2] #, special
                    
                    df.loc[(molecule, "%Diff"),
                        (fuel, condition, eqRatio)] = metrics[molecule][3] #, special



SKIP_FUELS = ["95-5", "85-15", "1-99"]
PLOT_FUELS = [f for f in FUEL if f not in SKIP_FUELS]

def avg_pct_diff_by_molecule(df, condition):
    sub = df.xs(condition, axis=1, level="Condition")           # columns: (Fuel Ratio, Equi Ratio)
    fuel_avg = sub.T.groupby(level="Fuel Ratio").mean().T        # avg across EQR -> one value per fuel per molecule
    return fuel_avg[PLOT_FUELS].reindex(index=MOLECULES, level="Molecule")

def plot_condition(df, condition, title, filename):
    data = avg_pct_diff_by_molecule(df, condition)
    plt.figure()
    for molecule in MOLECULES:
        y = data.loc[(molecule, "%Diff")].values
        plt.plot(PLOT_FUELS, y, marker="o", label=molecule)
    plt.xlabel("Fuel Ratio (NH3 -> H2)")
    plt.ylabel("Avg % Difference")
    plt.title(title)
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(filename)
    plt.show()

# plot_condition(df, "Atm", "Average %Diff vs Fuel Ratio (Atmospheric)", "atm_pct_diff.png")
# plot_condition(df, "Turb", "Average %Diff vs Fuel Ratio (Turbine)", "turb_pct_diff.png")

def avg_pct_diff_by_molecule_vs_eqr(df, condition):
    sub = df.xs(condition, axis=1, level="Condition")           # columns: (Fuel Ratio, Equi Ratio)
    eqr_avg = sub.T.groupby(level="Equi Ratio").mean().T         # avg across Fuel Ratio -> one value per EQR per molecule
    return eqr_avg.reindex(index=MOLECULES, level="Molecule")

def plot_condition_vs_eqr(df, condition, title, filename):
    data = avg_pct_diff_by_molecule_vs_eqr(df, condition)
    plt.figure()
    for molecule in MOLECULES:
        plt.plot(EQR, data.loc[(molecule, "%Diff"), EQR], marker="o", label=molecule)
    plt.xlabel("Equivalence Ratio")
    plt.ylabel("Avg % Difference")
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename)
    plt.show()

# plot_condition_vs_eqr(df, "Atm", "Average %Diff vs Equivalence Ratio (Atmospheric)", "atm_pct_diff_vs_eqr.png")
# plot_condition_vs_eqr(df, "Turb", "Average %Diff vs Equivalence Ratio (Turbine)", "turb_pct_diff_vs_eqr.png")


# import matplotlib.colors as mcolors

# atm = df.xs("Atm", axis=1, level="Condition")     # columns: (Fuel Ratio, Equi Ratio)
# turb = df.xs("Turb", axis=1, level="Condition")

# change = turb.abs() - atm.abs()                                # + means Turbine bigger, - means Atm bigger
# change.index = change.index.droplevel("Metric")    # rows now just Molecule
# change = change.reindex(index=MOLECULES)

# # red for positive (Turbine bigger), green for negative (Atm bigger)
# cmap = mcolors.LinearSegmentedColormap.from_list("green_white_red", ["green", "white", "red"])

# vmax = np.nanpercentile(change.abs().values, 90)

# styled = (
#     change.style
#     .format(lambda v: f"{v:+.1f}")
#     .background_gradient(cmap=cmap, vmin=-vmax, vmax=vmax)
#     .set_table_styles([
#         {"selector": "table", "props": [("border-collapse", "collapse")]},
#         {"selector": "th", "props": [("border", "1px solid black")]},
#         {"selector": "td", "props": [("border", "1px solid black")]},
#     ])
# )

# styled.to_html("turb_vs_atm_change.html")

filename = "tableWithColdTurbine.html"
df.to_html(filename)
#print(df)
#df.to_excel(f"{filename.split(".")[0]}.xlsx", merge_cells=True)

#save_pretty_html(df, filename)