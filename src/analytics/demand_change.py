import pandas as pd
import numpy as np
from datetime import date
import MySQLdb
import time

# Put this as 'True' if you're working on the algorithm and validating the results through the output csv
is_algorithm_development = False
umwteuro_down_threshold = -50000
umwteuro_up_percent_threshold = 10

headers = ["Division_short", "BL_short", "PL", "MD_Process", "SAMPLE_FLAG", "KONSI_FLAG", "HFG", "HFG_Desc", "CC_Region", "MC_ValueChain", "MainCustomer_Name", "SO_CLMPool", "CLM_Code", "SoldTo_No", "SoldTo_Name", "SoldTo_City", "SoldTo_Country", "ShipTo_No", "ShipTo_Name", "ShipTo_City", "Shipto_Country", "CPN_List", "SP_Cleaned", "SalesName", "FP_Plant", "PackageClass_PL", "PackageGroup_PL", "PackageClass_AGG_PL", "Product_Class_act", "SAP_AllocPolicy", "AKT_DAY", "Quarter", "MONAT", "Act_Month_flag", "Act_Quarter_flag", "Max_weekday_flag", "Act_day_flag", "Act_Last_day_flag", "Act_Last_week_flag", "Act_Last_4_week_flag", "Act_Last_day_week_4week_flag", "OOH_Pcs_WT_SC", "OOH_Euro_WT_SC", "OOH_Pcs_WT_CU", "OOH_Euro_WT_CU", "OOH_Pcs_AT_SC", "OOH_Euro_AT_SC", "OOH_Pcs_KT_SC", "OOH_Euro_KT_SC", "OOH_Pcs_KT_CU", "OOH_Euro_KT_CU", "UC_WT_OOH_Pcs_WT_SC", "UC_WT_OOH_Euro_WT_SC", "UC_WT_OOH_Pcs_WT_CU", "UC_WT_OOH_Euro_WT_CU", "UC_WT_OOH_Pcs_AT_SC", "UC_WT_OOH_Euro_AT_SC", "UC_WT_OOH_Pcs_KT_SC", "UC_WT_OOH_Euro_KT_SC", "UC_WT_OOH_Pcs_KT_CU", "UC_WT_OOH_Euro_KT_CU", "UM_ST", "UM_EURO", "OOHUM_WT_CU_pcs_actd", "OOHUM_WT_CU_Euro_actd", "OOHUM_WT_CU_pcs_lastd", "OOHUM_WT_CU_Euro_lastd", "OOHUM_WT_CU_pcs_lastw", "OOHUM_WT_CU_Euro_lastw", "OOHUM_WT_CU_pcs_last_4_w", "OOHUM_WT_CU_Euro_last_4_w", "OOHUM_AT_SC_pcs_actd", "OOHUM_AT_SC_Euro_actd", "OOHUM_AT_SC_pcs_lastd", "OOHUM_AT_SC_Euro_lastd", "OOHUM_AT_SC_pcs_lastw", "OOHUM_AT_SC_Euro_lastw", "OOHUM_AT_SC_pcs_last_4_w", "OOHUM_AT_SC_Euro_last_4_w", "UC_WT_OOH_Euro_WT_CU_actd", "UC_WT_OOH_Pcs_WT_CU_actd", "UC_WT_OOH_Euro_WT_CU_lastd", "UC_WT_OOH_Pcs_WT_CU_lastd", "UC_WT_OOH_Euro_WT_CU_lastw", "UC_WT_OOH_Pcs_WT_CU_lastw", "UC_WT_OOH_Euro_WT_CU_last_4_w", "UC_WT_OOH_Pcs_WT_CU_last_4_w", "UM_OOH_WT_CU_pcs", "UM_OOH_AT_SC_pcs"]
index = {"PL":2,"CLM_Code":12,"SoldTo_Name":14,"SalesName":23,"AKT_Day":30,"MONAT":32,"UM_WT":87, "UM_WT/EURO":88}
impt_headers = ["PL", "SO_CLMPool", "CLM_Code", "SoldTo_Name", "SalesName", "AKT_DAY", "Quarter", "MONAT", "OOH_Pcs_WT_CU", "OOH_Euro_WT_CU", "OOH_Pcs_AT_SC", "OOH_Euro_AT_SC", "UM_ST", "UM_EURO", "UM_OOH_WT_CU_pcs", "UM_OOH_AT_SC_pcs"]


def check_demand_period(recent_month):  # month refers to monat
    if int(recent_month[-2:]) != 12:
        recent_month_plus1 = recent_month[:-2] + str(int(recent_month[-2:])+1).zfill(2)
    else: recent_month_plus1 = str(int(recent_month[0:4])+1) + str(1).zfill(2)
    if int(recent_month[-2:]) != 11:
        recent_month_plus2 = recent_month_plus1[:-2] + str(int(recent_month_plus1[-2:])+1).zfill(2)
    else: recent_month_plus2 = str(int(recent_month_plus1[0:4])+1) + str(1).zfill(2)
    return int(recent_month), int(recent_month_plus1), int(recent_month_plus2)

#function takes in the most recent monat detected in the file, and outputs the monats for m-1, m and m+1. This will be in terms of weekats subsequently
#to be changed to weekats
def check_supply_period(recent_month):  # month refers to monat
    if recent_month[-2:] != "12":
        recent_month_plus1 = int(recent_month)+1
    else: recent_month_plus1 = str(int(recent_month[0:-2])+1) + str(1).zfill(2)
    if recent_month[-2:] != "01":
        recent_month_minus1 = int(recent_month)-1
    else: recent_month_minus1 = str(int(recent_month[0:-2])-1) + str(12)
    return int(recent_month_minus1), int(recent_month), int(recent_month_plus1)

#function that takes in a list of unique akt days found in the file, and outputs the most recent akt_day, as well as the friday before's akt_day for subsequent comparison
def check_comparison_dates(df_akt):    # find the date to compare against
    recent_akt = df['AKT_DAY'].max()
    recent_day_index = date.weekday(recent_akt.date())
    list_unique_AKTDays = np.sort(df['AKT_DAY'].unique())
    if int(list_unique_AKTDays[-1] - list_unique_AKTDays[-2])/86400000000000 == 1:
        last_akt4comparison = list_unique_AKTDays[-(recent_day_index+2)]    #can be improved to detect a friday instead, as a more accurate measure
    else:
        last_akt4comparison = list_unique_AKTDays[-2]
    return recent_akt, last_akt4comparison

def change_percentage(this, last):
    if (this == np.nan) & (last==np.nan):
        calc = np.nan
    elif (this==0.0) & (last==0.0):
        calc= 0
    else:
        calc = round( (this - last)/(float(this + last)) * 100, 1)
    return calc

def calc_demand_change(df, is_algorithm_development):
    df['UM_WT_Euro'] =df['UM_EURO'].replace('nan', 0)+df['OOH_Euro_WT_CU'].replace('nan', 0)
    df['UM_WT_Pcs'] =df['UM_ST'].replace('nan', 0)+df['OOH_Pcs_WT_CU'].replace('nan', 0)
    df['AKT_DAY'] = pd.to_datetime(df['AKT_DAY'], dayfirst=True)
    recent_akt, last_akt = check_comparison_dates(df['AKT_DAY'])
    recent_month = str(recent_akt)[0:4]+str(recent_akt)[5:7]
    m, m_plus1, m_plus2 = check_demand_period(recent_month)
    demand_records = []

    for clm in sorted(df["CLM_Code"].fillna("Unknowns").unique()):
        for soldtoname in sorted(df['SoldTo_Name'][df['CLM_Code']==clm].fillna("Unknowns").unique()):
            for salesname in df['SalesName'][(df['CLM_Code']==clm) & (df["SoldTo_Name"]==soldtoname)].fillna('Unknowns').unique():
                for monat in [m, m_plus1, m_plus2]:

                    # UM_WT_Pcs (Will not be involved in the SC/Alert Algo)
                    if len(df["UM_WT_Pcs"][(df['CLM_Code']==clm) & (df['SoldTo_Name']==soldtoname) & (df["SalesName"]==salesname) & (df["MONAT"]==monat) & (df['AKT_DAY']==recent_akt)]) == 0:
                        this_umwtpcs = 0
                    else:
                        this_umwtpcs = df.loc[(df['CLM_Code']==clm) & (df['SoldTo_Name']==soldtoname) & (df["SalesName"]==salesname) & (df["MONAT"]==monat) & (df['AKT_DAY']==recent_akt), "UM_WT_Pcs"].replace('nan',0).sum()
                    if len(df["UM_WT_Pcs"][(df['CLM_Code']==clm) & (df['SoldTo_Name']==soldtoname) & (df["SalesName"]==salesname) & (df["MONAT"]==monat) & (df['AKT_DAY']==last_akt)]) == 0:
                        last_umwtpcs = 0
                    else:
                        last_umwtpcs = df.loc[(df['CLM_Code']==clm) & (df['SoldTo_Name']==soldtoname) & (df["SalesName"]==salesname) & (df["MONAT"]==monat) & (df['AKT_DAY']==last_akt), "UM_WT_Pcs"].replace('nan',0).sum()
                    diff_umwtpcs = round(this_umwtpcs - last_umwtpcs,0)
                    diff_umwtpcs_percentage = change_percentage(this_umwtpcs, last_umwtpcs)

                    # UM_WT_Euro
                    if len(df["UM_WT_Euro"][(df['CLM_Code']==clm) & (df['SoldTo_Name']==soldtoname) & (df["SalesName"]==salesname) & (df["MONAT"]==monat) & (df['AKT_DAY']==recent_akt)]) == 0:
                        this_umwteuro = 0
                    else:
                        this_umwteuro = df.loc[(df['CLM_Code']==clm) & (df['SoldTo_Name']==soldtoname) & (df["SalesName"]==salesname) & (df["MONAT"]==monat) & (df['AKT_DAY']==recent_akt), "UM_WT_Euro"].replace('nan',0).sum()
                    if len(df["UM_WT_Euro"][(df['CLM_Code']==clm) & (df['SoldTo_Name']==soldtoname) & (df["SalesName"]==salesname) & (df["MONAT"]==monat) & (df['AKT_DAY']==last_akt)]) == 0:
                        last_umwteuro = 0
                    else:
                        last_umwteuro = df.loc[(df['CLM_Code']==clm) & (df['SoldTo_Name']==soldtoname) & (df["SalesName"]==salesname) & (df["MONAT"]==monat) & (df['AKT_DAY']==last_akt), "UM_WT_Euro"].replace('nan',0).sum()
                    diff_umwteuro = round(this_umwteuro - last_umwteuro,2)
                    diff_umwteuro_percent = change_percentage(this_umwteuro, last_umwteuro)

                    alert_flag = 1 if ((diff_umwteuro < umwteuro_down_threshold) or (diff_umwteuro_percent > umwteuro_up_percent_threshold)) else 0

                    if np.isnan(diff_umwteuro_percent):
                        pass

                    if is_algorithm_development:
                        demand_records.append({"clm_code":clm, "soldtoname": soldtoname, "salesname":salesname, "monat":monat, "alert_flag": alert_flag, "last_umwteuro_amt":last_umwteuro, "this_umwteuro_amt": this_umwteuro, "diff_umwteuro":diff_umwteuro, "sc_diff_umwteuro_percent": diff_umwteuro_percent})
                    else:
                        cursor.execute("INSERT INTO dashboard_demandchangerecord(clm_code, soldtoname, salesname, monat, akt_day, last_umwteuro_amt, this_umwteuro_amt, diff_umwteuro, sc_diff_umwteuro_percent, alert_flag) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (clm, soldtoname, salesname, monat, recent_akt, last_umwteuro, this_umwteuro, diff_umwteuro, diff_umwteuro_percent, alert_flag))
    return demand_records


#################### Above is Need 1 and Structural Change ####################
#################### Below is Business Performance ####################
def calculate_bp(df, is_algorithm_development):
    df['AKT_DAY'] = pd.to_datetime(df['AKT_DAY'], dayfirst=True)
    recent_akt, last_akt = check_comparison_dates(df['AKT_DAY'])
    recent_monat = str(recent_akt)[0:4]+str(recent_akt)[5:7]
    if (str(recent_monat)[-2:] == "10") or (str(recent_monat)[-2:] == "11") or (str(recent_monat)[-2:] == "12"):
        current_quarter = str(int(str(recent_monat)[0:-2])+1) + "Q1"
        next_quarter = str(int(str(recent_monat)[0:-2])+1) + "Q2"
    else:
        current_quarter = str(recent_monat)[0:-2] + "Q" + str(int(str(recent_monat)[-2:])/3 + int(float(str(recent_monat)[-2:])%3>0) + 1)
        if (str(recent_monat)[-2:] == "07") or (str(recent_monat)[-2:] == "08") or (str(recent_monat)[-2:] == "09"):
            next_quarter = str(int(str(recent_monat)[0:-2])+1) + "Q1"
        else:
            next_quarter = str(recent_monat)[0:-2] + "Q" + str((int(str(recent_monat)[-2:])+3)/3 + int(float(str(recent_monat)[-2:])%3>0) + 1)

    bp = []

    # Demand
    df['UM_WT_Euro'] =df['UM_EURO'].replace("nan",0)+df['OOH_Euro_WT_CU'].replace("nan",0)
    df['UM_WT_Euro'] = df['UM_WT_Euro'].replace("nan",0)
    m, m_plus1, m_plus2 = check_demand_period(recent_monat)
    df['SumUMWTEuro_CLM_SoldToName'] = df.groupby(['CLM_Code', 'SoldTo_Name','AKT_DAY','Quarter'])['UM_WT_Euro'].transform('sum')
    df['SumUMWTEuro_CLM_SoldToName'] = df['SumUMWTEuro_CLM_SoldToName'].replace('nan', 0)

    for clm in sorted(df["CLM_Code"].fillna("Unknowns").unique()):
        for soldtoname in sorted(df['SoldTo_Name'][df['CLM_Code']==clm].fillna("Unknowns").unique()):
            # Demand

            # Read the UMWTEuro values for current Quarter #
            if len(df["SumUMWTEuro_CLM_SoldToName"][(df['CLM_Code']==clm) & (df['SoldTo_Name']==soldtoname) & (df["Quarter"]==current_quarter) & (df['AKT_DAY']==recent_akt)]) == 0:
                BP_demand_thisakt_thisQ = 0.0
            else:
                BP_demand_thisakt_thisQ = df["SumUMWTEuro_CLM_SoldToName"][(df['CLM_Code']==clm) & (df['SoldTo_Name']==soldtoname) & (df["Quarter"]==current_quarter) & (df['AKT_DAY']==recent_akt)].max()

            if len(df["SumUMWTEuro_CLM_SoldToName"][(df['CLM_Code']==clm) & (df['SoldTo_Name']==soldtoname) & (df["Quarter"]==current_quarter) & (df['AKT_DAY']==last_akt)]) == 0:
                BP_demand_lastakt_thisQ = 0.0
            else:
                BP_demand_lastakt_thisQ = df["SumUMWTEuro_CLM_SoldToName"][(df['CLM_Code']==clm) & (df['SoldTo_Name']==soldtoname) & (df["Quarter"]==current_quarter) & (df['AKT_DAY']==last_akt)].max()

            # Calculate BP values for current Quarter #
            if BP_demand_lastakt_thisQ == 0 and BP_demand_thisakt_thisQ==0:
                bp_demand_this_quarter = "0.00"
            elif BP_demand_lastakt_thisQ == 0 and BP_demand_thisakt_thisQ>0:
                bp_demand_this_quarter = "NEW"
            else:
                bp_demand_this_quarter = str(round(float(BP_demand_thisakt_thisQ - BP_demand_lastakt_thisQ)*100/(float(BP_demand_lastakt_thisQ)),2))
                if float(bp_demand_this_quarter) < -0.001:
                    bp_demand_this_quarter == "0.00"

            # Read the UMWTEuro values for next Quarter #
            if len(df["SumUMWTEuro_CLM_SoldToName"][(df['CLM_Code']==clm) & (df['SoldTo_Name']==soldtoname) & (df["Quarter"]==next_quarter) & (df['AKT_DAY']==recent_akt)]) == 0:
                BP_demand_thisakt_nextQ = 0.0
            else:
                BP_demand_thisakt_nextQ = df["SumUMWTEuro_CLM_SoldToName"][(df['CLM_Code']==clm) & (df['SoldTo_Name']==soldtoname) & (df["Quarter"]==next_quarter) & (df['AKT_DAY']==recent_akt)].max()

            if len(df["SumUMWTEuro_CLM_SoldToName"][(df['CLM_Code']==clm) & (df['SoldTo_Name']==soldtoname) & (df["Quarter"]==next_quarter) & (df['AKT_DAY']==last_akt)]) == 0:
                BP_demand_lastakt_nextQ = 0.0
            else:
                BP_demand_lastakt_nextQ = df["SumUMWTEuro_CLM_SoldToName"][(df['CLM_Code']==clm) & (df['SoldTo_Name']==soldtoname) & (df["Quarter"]==next_quarter) & (df['AKT_DAY']==last_akt)].max()

            # Calculate BP values for next Quarter #
            if BP_demand_lastakt_nextQ == 0.0 and BP_demand_thisakt_nextQ==0.0:
                bp_demand_next_quarter = "0.0"
            elif BP_demand_lastakt_nextQ == 0.0 and BP_demand_thisakt_nextQ>0.0:
                bp_demand_next_quarter = "NEW"
            else:
                bp_demand_next_quarter = str(round(float(BP_demand_thisakt_nextQ - BP_demand_lastakt_nextQ)*100/(float(BP_demand_lastakt_nextQ)),2))
                if float(bp_demand_next_quarter) < -0.001:
                    bp_demand_next_quarter == "0.0"

            if is_algorithm_development:
                bp.append({"clm":clm,"soldtoname":soldtoname,"bp_this_quarter":bp_demand_this_quarter, "bp_next_quarter": bp_demand_next_quarter, "current_quarter":current_quarter, "next_quarter": next_quarter})
            else:
                cursor.execute("INSERT INTO dashboard_businessperformance(clm_code, soldtoname, bp_demand_this_quarter, bp_demand_next_quarter, current_quarter, next_quarter, bp_supply, bp_order) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (clm, soldtoname, bp_demand_this_quarter, bp_demand_next_quarter, current_quarter, next_quarter, 0, 0))

    return bp
##################### End Functions ########################

if is_algorithm_development:
    start = time.time()
    import csv
    # df = pd.read_csv('order development_Z02 and Z04_3Q (2-12 Jun daily snapshot).csv', parse_dates=True)
    df = pd.read_csv('/srv/website/data/order_development_Z02_Z04_3Q_2-12jun_daily.csv', encoding="ISO-8859-1", parse_dates=True)
    end = time.time()
    print("Time taken to read csv: {0:.6f} seconds ".format(end-start))

    start = time.time()
    # toCSV = calc_demand_change(df,is_algorithm_development)
    toCSV = calculate_bp(df,is_algorithm_development)
    keys = toCSV[0].keys()
    # with open('output_need1.csv', 'wb') as output_file:
    with open('output_need1.csv', 'w') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(toCSV)
    end = time.time()
    print("Time taken to run demand change algorithm: {0:.6f} seconds ".format(end-start))

else:
    start = time.time()
    df = pd.read_csv('/srv/website/data/order_development_Z02_Z04_3Q_2-12jun_daily.csv', encoding="ISO-8859-1", parse_dates=True)
    end = time.time()
    print("Time taken to read csv: {0:.6f} seconds ".format(end-start))

    mydb = MySQLdb.connect(
        host='localhost',
        user='user',
        passwd='password',
        db='djangodb'
    )

    cursor = mydb.cursor()
    cursor.execute("truncate dashboard_demandchangerecord")
    cursor.execute("truncate dashboard_businessperformance")

    start = time.time()
    calc_demand_change(df, is_algorithm_development)
    end = time.time()
    print("Time taken to run demand change algorithm: {0:.6f} seconds ".format(end-start))

    start = time.time()
    calculate_bp(df, is_algorithm_development)
    end = time.time()
    print("Time taken to run bp algorithm: {0:.6f} seconds ".format(end-start))

    mydb.commit()
    cursor.close()
