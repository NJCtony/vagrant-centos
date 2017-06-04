import pandas as pd
import numpy as np
from datetime import date
import MySQLdb
import time


impt_headers = ["PL", "SO_CLMPool", "CLM_Code", "SoldTo_Name", "SalesName", "AKT_DAY", "Quarter", "MONAT", "OOH_Pcs_WT_CU", "OOH_Euro_WT_CU", "OOH_Pcs_AT_SC", "OOH_Euro_AT_SC", "UM_ST", "UM_EURO", "UM_OOH_WT_CU_pcs", "UM_OOH_AT_SC_pcs"]


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
def check_comparison_dates(df_akt):
    recent_akt = df['AKT_DAY'].max()
    recent_day_index = date.weekday(recent_akt.date())
    list_unique_AKTDays = np.sort(df['AKT_DAY'].unique())
    if int(list_unique_AKTDays[-1] - list_unique_AKTDays[-2])/86400000000000 == 1:
        last_akt4comparison = list_unique_AKTDays[-(recent_day_index+2)]    #can be improved to detect a friday instead, as a more accurate measure
    else:
        last_akt4comparison = list_unique_AKTDays[-2]
    return recent_akt, last_akt4comparison

def calc_supply_change_percentage(this, last):
    #calc = round((( 1 + ((this - last)/(float(this + last)/2)) ) * 100),1)
    baseline = 100
    #print this, last, type(this), type(last)
    if (this == np.nan) & (last==np.nan):
        calc = np.nan
    elif (this==0.0) & (last==0.0):
        calc= baseline
    else:
        calc = round(baseline+( ((this - last)/(float(this + last)))* 100),1)
    return calc


###############################################################
########## Below is Need 2 and Structural Change ##############
###############################################################
#   BP and alerts account for the period across W, W+1, W-1   #
#   SC account for each W                                  #
###############################################################

def need2(df):
    df['UM_WT_Pcs'] =df['UM_ST'].replace('nan', 0)+df['OOH_Pcs_WT_CU'].replace('nan', 0)
    df['UM_AT_Pcs'] =df['UM_ST'].replace('nan', 0)+df['OOH_Pcs_AT_SC'].replace('nan', 0)
    df['AKT_DAY'] = pd.to_datetime(df['AKT_DAY'], dayfirst=True)
    recent_akt, last_akt = check_comparison_dates(df['AKT_DAY'])
    recent_month = str(recent_akt)[0:4]+str(recent_akt)[5:7]
    m_minus1, m, m_plus1 = check_supply_period(recent_month)
    alerts_n2 = []

    for clm in sorted(df["CLM_Code"].unique()):
        for soldtoname in sorted(df['SoldTo_Name'][df['CLM_Code']==clm].unique()):
            for salesname in df['SalesName'][(df['CLM_Code']==clm) & (df["SoldTo_Name"]==soldtoname)].fillna("UNKNOWN").unique():

                this_umwtpcs_3WPeriod = df.loc[(df['CLM_Code']==clm) & (df['SoldTo_Name']==soldtoname) & (df["SalesName"]==salesname) & (df["MONAT"].isin([int(m_minus1),int(m),int(m_plus1)])) & (df['AKT_DAY']==recent_akt),"UM_WT_Pcs"].replace('nan',0).sum()
                last_umwtpcs_3WPeriod = df.loc[(df['CLM_Code']==clm) & (df['SoldTo_Name']==soldtoname)& (df["SalesName"]==salesname) & (df["MONAT"].isin([int(m_minus1),int(m),int(m_plus1)])) & (df['AKT_DAY']==last_akt),"UM_WT_Pcs"].replace('nan',0).sum()
                diff_umwtpcs_3WPeriod = round(this_umwtpcs_3WPeriod - last_umwtpcs_3WPeriod,0)

                this_umatpcs_3WPeriod = df.loc[(df['CLM_Code']==clm) & (df['SoldTo_Name']==soldtoname) & (df["SalesName"]==salesname) & (df["MONAT"].isin([int(m_minus1),int(m),int(m_plus1)])) & (df['AKT_DAY']==recent_akt), "UM_AT_Pcs"].replace('nan',0).sum()
                last_umatpcs_3WPeriod = df.loc[(df['CLM_Code']==clm) & (df['SoldTo_Name']==soldtoname)& (df["SalesName"]==salesname) & (df["MONAT"].isin([int(m_minus1),int(m),int(m_plus1)])) & (df['AKT_DAY']==last_akt), "UM_AT_Pcs"].replace('nan',0).sum()
                diff_umatpcs_3WPeriod = round(this_umatpcs_3WPeriod - last_umatpcs_3WPeriod,0)
                diff_umatpcs_3WPeriod_percentage = calc_supply_change_percentage(this_umatpcs_3WPeriod, last_umatpcs_3WPeriod)

                if diff_umatpcs_3WPeriod < 0 and diff_umatpcs_3WPeriod < diff_umwtpcs_3WPeriod:
                    alert_flag = 1
                    alert_percentage = diff_umatpcs_3WPeriod_percentage
                else:
                    alert_flag = 0
                    alert_percentage = 0


                ### Structural Change Algo ###
                for monat in [m_minus1, m, m_plus1]:
                    this_umatpcs_list = df["UM_AT_Pcs"][(df['CLM_Code']==clm) & (df['SoldTo_Name']==soldtoname) & (df["SalesName"]==salesname) & (df["MONAT"]==monat) & (df['AKT_DAY']==recent_akt)].values
                    if len(this_umatpcs_list) == 0:
                        this_umatpcs = 0
                    else:
                        this_umatpcs = this_umatpcs_list.max()

                    last_umatpcs_list = df["UM_AT_Pcs"][(df['CLM_Code']==clm) & (df['SoldTo_Name']==soldtoname) & (df["SalesName"]==salesname) & (df["MONAT"]==monat) & (df['AKT_DAY']==last_akt)].values
                    if len(last_umatpcs_list) == 0:
                        last_umatpcs = 0
                    else:
                        last_umatpcs = last_umatpcs_list.max()

                    diff_umatpcs = round(this_umatpcs - last_umatpcs,0)
                    diff_umatpcs_percentage = calc_supply_change_percentage(this_umatpcs, last_umatpcs)

                    if np.isnan(diff_umatpcs_percentage):
                        pass
                    else:
                        if alert_flag == 1:
                            # alerts_n2.append({"clm_code":clm, "soldtoname": soldtoname, "salesname":salesname, "monat":monat, "akt_day":recent_akt, "alert_flag":alert_flag, "alert_percentage": alert_percentage, "last_umatpcs_amt":last_umatpcs, "this_umatpcs_amt": this_umatpcs, "diff_umatpcs":diff_umatpcs, "[SC]_diff_umatpcs_%": diff_umatpcs_percentage, "diff_umwtpcs_3WPeriod": diff_umwtpcs_3WPeriod, "diff_umatpcs_3WPeriod": diff_umatpcs_3WPeriod, "this_umatpcs_3WPeriod":this_umatpcs_3WPeriod, "last_umatpcs_3WPeriod":last_umatpcs_3WPeriod})

                            cursor.execute("INSERT INTO dashboard_supplychangerecord(clm_code, soldtoname, salesname, monat, akt_day, this_umatpcs_3WPeriod, last_umatpcs_3WPeriod, diff_umatpcs_3WPeriod, this_umatpcs_amt, last_umatpcs_amt, diff_umatpcs, sc_diff_umatpcs_percentage, diff_umwtpcs_3WPeriod, alert_percentage, alert_flag) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (clm, soldtoname, salesname, monat, recent_akt, this_umatpcs_3WPeriod, last_umatpcs_3WPeriod, diff_umatpcs_3WPeriod, this_umatpcs, last_umatpcs, diff_umatpcs, diff_umatpcs_percentage, diff_umwtpcs_3WPeriod, alert_percentage, alert_flag))

                            alert_flag = 0
                            alert_percentage = 0

                        else:
                            # alerts_n2.append({"clm_code":clm, "soldtoname": soldtoname, "salesname":salesname, "monat":monat, "akt_day":recent_akt, "alert_flag":alert_flag, "alert_percentage": alert_percentage, "last_umatpcs_amt":last_umatpcs, "this_umatpcs_amt": this_umatpcs, "diff_umatpcs":diff_umatpcs, "[SC]_diff_umatpcs_%": diff_umatpcs_percentage, "diff_umwtpcs_3WPeriod": diff_umwtpcs_3WPeriod, "diff_umatpcs_3WPeriod": diff_umatpcs_3WPeriod, "this_umatpcs_3WPeriod":this_umatpcs_3WPeriod, "last_umatpcs_3WPeriod":last_umatpcs_3WPeriod})
                            cursor.execute("INSERT INTO dashboard_supplychangerecord(clm_code, soldtoname, salesname, monat, akt_day, this_umatpcs_3WPeriod, last_umatpcs_3WPeriod, diff_umatpcs_3WPeriod, this_umatpcs_amt, last_umatpcs_amt, diff_umatpcs, sc_diff_umatpcs_percentage, diff_umwtpcs_3WPeriod, alert_percentage, alert_flag) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (clm, soldtoname, salesname, monat, recent_akt, this_umatpcs_3WPeriod, last_umatpcs_3WPeriod, diff_umatpcs_3WPeriod, this_umatpcs, last_umatpcs, diff_umatpcs, diff_umatpcs_percentage, diff_umwtpcs_3WPeriod, alert_percentage, alert_flag))

    return alerts_n2

##################### End Functions ########################


start = time.time()
df = pd.read_csv('/srv/website/data/Need1_K03.csv', encoding="ISO-8859-1", parse_dates=True)
end = time.time()
print("Time taken to read csv: {0:.6f} seconds ".format(end-start))

mydb = MySQLdb.connect(
    host='localhost',
    user='user',
    passwd='password',
    db='djangodb'
)

cursor = mydb.cursor()
cursor.execute("truncate dashboard_supplychangerecord")

start = time.time()
# import csv
# toCSV = need2(df)
# keys = toCSV[0].keys()
# with open('output_need2.csv', 'w') as output_file:
#    dict_writer = csv.DictWriter(output_file, keys)
#    dict_writer.writeheader()
#    dict_writer.writerows(toCSV)
need2(df)
end = time.time()
print("Time taken to run supply change algorithm: {0:.6f} seconds ".format(end-start))


mydb.commit()
cursor.close()
