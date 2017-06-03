import pandas as pd
import numpy as np
from datetime import date
import MySQLdb
import time


### Function to identify 3 main periods: ####################################################################
#  (1) 12 MONATs back, (2) 3 MONATs back, (3) Current + 2 MONATs ######
#############################################################################################################

def check_period_need(df):
    for i in reversed(list(df)):
        if i[:2]=="20":           #identification of the latest-past MONAT, ie current 201703, it identifies 201702
            monat_minus1 = i
            break

    monat_monthlist = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
    last_index = monat_monthlist.index(monat_minus1[-2:])
    current_index = last_index+1

    # Group MONATs that belong to the past 12 months
    monat_checkback_yr = []
    if last_index <= 11:
        for month in monat_monthlist[last_index+1-12:]:
            monat_checkback_yr.append(int(monat_minus1[0:3] + str(int(monat_minus1[3:4])-1) + month))
        if last_index != 11:
            for month2 in monat_monthlist[0:last_index+1]:
                monat_checkback_yr.append(int(monat_minus1[0:3] + str(int(monat_minus1[3:4])) + month2))
    else:
        for month in monat_monthlist:
            monat_checkback_yr.append(int(monat_minus1[0:3] + str(int(monat_minus1[3:4])) + month2))

    # Group MONATs that belong to the past 3 months
    monat_checkback_3m = []
    if last_index > 2:
        for month in monat_monthlist[last_index-2:last_index+1]:
            monat_checkback_3m.append(int(monat_minus1[0:3] + str(int(monat_minus1[3:4])) + month))
    else:
        if last_index < 2:
            for month2 in monat_monthlist[last_index-2:]:
                monat_checkback_3m.append(int(monat_minus1[0:3] + str(int(monat_minus1[3:4])-1) + month2))
        for month in monat_monthlist[0:last_index+1]:
            monat_checkback_3m.append(int(monat_minus1[0:3] + str(int(monat_minus1[3:4])) + month))

    # Group MONATs that belong to the the current, or the next 2 months
    monat_checkfwd_2m = []
    if current_index <= 9:
        for month in monat_monthlist[current_index:current_index+1+2]:
            monat_checkfwd_2m.append(int(monat_minus1[0:3] + str(int(monat_minus1[3:4])) + month))
    else:
        for month in monat_monthlist[current_index:]:
            monat_checkfwd_2m.append(int(monat_minus1[0:3] + str(int(monat_minus1[3:4])) + month))
        for month in monat_monthlist[:current_index+2+1-12]:
            monat_checkfwd_2m.append(int(monat_minus1[0:3] + str(int(monat_minus1[3:4])+1) + month))
    #return monat_checkfwd_2m

    return {"pastyr":monat_checkback_yr, "past3m": monat_checkback_3m, "nowplus2": monat_checkfwd_2m}



################################## Main Function ##############################################
# It firstly checks if there are any recent orders in the last 3 MONATs,   [At least 1 order in the past 3 MONATs]
# then checks if there have been consistent ordering in the last 12 MONATs,   [At least 6 orders in the past 12 MONATs]
# finally calculates the MEAN, and STANDARD DEVIATION
# applying the threshold of MEAN+3*STANDARD DEVIATION to any orders in the current, or future 2 MONATs, where applicable.
#############################################################################################################

def need3(filename):
    df = pd.read_csv(filename, encoding="ISO-8859-1", parse_dates=True, header=1)
    if "bills" not in list(df):
        ##############################################################################################
        ######### Error Handling if the entire table is not copied and pasted in its entirety ########
        df = pd.read_csv(filename, encoding="ISO-8859-1", parse_dates=True, header=0)
        if "bills" not in list(df):            #Return error if the format of file is not acceptable
            return "ERROR! COLUMN HEADERS CANNOT BE READ!"
        else: pass
        ##############################################################################################
    else:
        pass

    df['bills'] = pd.to_numeric(df['bills'].str.replace(',', ''))
    df['today'] = pd.to_numeric(df['today'].str.replace(',', ''))
    df['bills_today_WTCU'] = df.bills.fillna(0)+df.today.fillna(0)

    monat_dict = check_period_need(df)
    current_m = sorted(monat_dict["nowplus2"])[0]
    nowplus2 = set(sorted(monat_dict["nowplus2"]))
    past3m = set(sorted(monat_dict["past3m"]))
    pastyr = set(sorted(monat_dict["pastyr"]))

    alerts_n3 = []

    for soldtoname in sorted(df["SoldTo_Name"].unique()):
        for salesname in sorted(df['SalesName'][df['SoldTo_Name']==soldtoname].unique()):
            monatlist = sorted(df['MONAT'][(df['SoldTo_Name']==soldtoname) & (df["SalesName"]==salesname)].unique())
            nowtoMplus2 = set(monatlist).intersection(nowplus2)
            if len(nowtoMplus2) >= 1:     #if there is an order within the period of [M, M+1, M+2]
                past3monat = set(monatlist).intersection(past3m)
                if len(past3monat) >= 1:     #if there is at least an order in the last 3 MONATs
                    pastyrmonat = set(monatlist).intersection(pastyr)
                    if len(pastyrmonat) >= 6:    #if there are at least 6 orders in the last 1 year
                        average = df["bills_today_WTCU"][(df['SoldTo_Name']==soldtoname) & (df['SalesName']==salesname) & (df["MONAT"].isin(pastyr))].replace(0,np.nan).mean()
                        stddev = df["bills_today_WTCU"][(df['SoldTo_Name']==soldtoname) & (df['SalesName']==salesname) & (df["MONAT"].isin(pastyr))].replace(0,np.nan).std()

                        for month in nowtoMplus2:
                            m_wtpcs = df["bills_today_WTCU"][(df['SoldTo_Name']==soldtoname) & (df["SalesName"]==salesname) & (df["MONAT"]==month)].max()
                            if m_wtpcs > 0:
                                diff_rate = m_wtpcs - average
                                num_sd_diff = 0 if (abs(diff_rate) < 0.0001 or stddev < 0.0001) else round((diff_rate/stddev), 2)   #identifies how many std dev the order size is from the mean
                                if (m_wtpcs > (average+3.0*stddev)) or (m_wtpcs < (average-3*stddev)):
                                    alert_flag = 1
                                    # alerts_n3.append({"soldtoname": soldtoname, "salesname":salesname, "monat":month, "alert_flag": alert_flag,  "wtpcs_amt":m_wtpcs, "average": average, "num_sd_diff": num_sd_diff})
                                    cursor.execute("INSERT INTO dashboard_needthreerecord(soldtoname, salesname, monat, wtpcs_amt, average, num_sd_diff, alert_flag) VALUES (%s, %s, %s, %s, %s, %s, %s)", (soldtoname, salesname, month, m_wtpcs, average, num_sd_diff, alert_flag))

    return alerts_n3



##################### End Functions ########################

#filename = 'Need 3_K03.csv'
filename = '/srv/website/data/Need3_K03.csv'

mydb = MySQLdb.connect(
    host='localhost',
    user='user',
    passwd='password',
    db='djangodb'
)

cursor = mydb.cursor()
cursor.execute("truncate dashboard_needthreerecord")
start = time.time()
need3(filename)
end = time.time()
print("Time taken to run need3 algorithm: {0:.6f} seconds ".format(end-start))

mydb.commit()
cursor.close()
