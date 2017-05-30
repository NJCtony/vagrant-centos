import pandas as pd
import numpy as np
from datetime import date
import MySQLdb
import time


def check_period_need(df):  # month refers to monat
    if "SoldTo_Name" not in list(df): return "ERROR! FILE TYPE NOT SUITABLE!"
    else:
        for i in reversed(list(df)):
            if i[:2]=="20":
                monat_minus1 = i
                break

    monat_monthlist = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]

    last_index = monat_monthlist.index(monat_minus1[-2:])

    monat_checkback_yr = []
    if last_index <= 11:
        for month in monat_monthlist[last_index+1-12:]:
            monat_checkback_yr.append(int(monat_minus1[0:3] + str(int(monat_minus1[3:4])-1) + month))
        for month2 in monat_monthlist[:last_index+1]:
            monat_checkback_yr.append(int(monat_minus1[0:3] + str(int(monat_minus1[3:4])) + month2))
    else:
        for month in monat_monthlist:
            monat_checkback_yr.append(int(monat_minus1[0:3] + str(int(monat_minus1[3:4])) + month2))

    monat_checkback_3m = []
    if last_index <= 11:
        for month in monat_monthlist[last_index+1-3:]:
            monat_checkback_3m.append(int(monat_minus1[0:3] + str(int(monat_minus1[3:4])-1) + month))
        for month2 in monat_monthlist[:last_index+1]:
            monat_checkback_3m.append(int(monat_minus1[0:3] + str(int(monat_minus1[3:4])) + month2))
    else:
        for month in monat_monthlist:
            monat_checkback_3m.append(int(monat_minus1[0:3] + str(int(monat_minus1[3:4])) + month2))

    current_index = last_index+1
    if current_index+1 != 12:
        monat_current = monat_minus1[:-2] + monat_monthlist[current_index]
    else: monat_current = monat_minus1[0:3] + str(int(monat_minus1[3:4])+1) + monat_monthlist[1]

    next1_index = current_index+1
    if next1_index != 12:
        monat_plus1 = monat_current[:-2] + monat_monthlist[next1_index]
    else: monat_plus1 = monat_current[0:3] + str(int(monat_current[3:4])+1) + str(1).zfill(2)

    next2_index = next1_index+1
    if next2_index != 12:
        monat_plus2 = monat_plus1[:-2] + monat_monthlist[next2_index]
    else: monat_plus2 = monat_plus1[0:3] + str(int(monat_plus1[3:4])+1) + str(1).zfill(2)

    monat_tocheck = [int(monat_current), int(monat_plus1), int(monat_plus2)]
    return {"pastyr":monat_checkback_yr, "past3m": monat_checkback_3m, "nowplus2": monat_tocheck}





def need3(df):
    df['bills'] = pd.to_numeric(df['bills'].str.replace(',', ''))
    df['today'] = pd.to_numeric(df['today'].str.replace(',', ''))
    df['bills_today_WTCU'] = df.bills.fillna(0)+df.today.fillna(0)

    monat_dict = check_period_need(df)
    current_m = sorted(monat_dict["nowplus2"])[0]
    nowplus2 = set(sorted(monat_dict["nowplus2"]))
    past3m = set(sorted(monat_dict["past3m"]))
    pastyr = set(sorted(monat_dict["pastyr"]))

    alerts_n3 = []
    summ=0

    for soldtoname in sorted(df["SoldTo_Name"].unique()):
        for salesname in sorted(df['SalesName'][df['SoldTo_Name']==soldtoname].unique()):
            monatlist = sorted(df['MONAT'][(df['SoldTo_Name']==soldtoname) & (df["SalesName"]==salesname)].unique())
            nowtoMplus2 = set(monatlist).intersection(nowplus2)
            if len(nowtoMplus2) >= 1:
                past3monat = set(monatlist).intersection(past3m)
                if len(past3monat) >= 1:
                    pastyrmonat = set(monatlist).intersection(pastyr)
                    if len(pastyrmonat) >= 6:
                        #average = np.mean(list(past3monat))
                        average = df["bills_today_WTCU"][(df['SoldTo_Name']==soldtoname) & (df['SalesName']==salesname) & (df["MONAT"].isin(past3monat))].mean()
                        stddev = df["bills_today_WTCU"][(df['SoldTo_Name']==soldtoname) & (df['SalesName']==salesname) & (df["MONAT"].isin(past3monat))].std()

                        for month in nowtoMplus2:
                            m_wtpcs = df["bills_today_WTCU"][(df['SoldTo_Name']==soldtoname) & (df["SalesName"]==salesname) & (df["MONAT"]==month)].max()
                            if m_wtpcs > 0:
                                diff_rate = m_wtpcs - average
                                percentage_rate = round((((m_wtpcs - average)/(m_wtpcs+average))) * 100, 2)
                                summ += diff_rate
                                if (diff_rate > average+3*stddev) or (diff_rate < average-3*stddev) and (abs(percentage_rate) > 20) :
                                    type_need = "Need 3"
                                    description = "Deviation by " + str(percentage_rate) + " %"
                                    # alerts_n3.append({"soldtoname": soldtoname, "salesname":salesname, "monat":month, "type": type_need, "description": description, "wtpcs_amt":m_wtpcs, "average": average})
                                    cursor.execute("INSERT INTO dashboard_needthreerecord(soldtoname, salesname, monat, wtpcs_amt, average, alert_type, alert_description) VALUES (%s, %s, %s, %s, %s, %s, %s)", (soldtoname, salesname, month, m_wtpcs, average, type_need, description))

    return alerts_n3


##################### End Functions ########################

start = time.time()
df = pd.read_csv('/srv/website/data/Need3_K03.csv', encoding="ISO-8859-1", parse_dates=True, header=1)
end = time.time()
print("Time taken to read csv: {0:.6f} seconds ".format(end-start))

mydb = MySQLdb.connect(
    host='localhost',
    user='user',
    passwd='password',
    db='djangodb'
)

cursor = mydb.cursor()
cursor.execute("truncate dashboard_needthreerecord")
start = time.time()
need3(df)
end = time.time()
print("Time taken to run need3 algorithm: {0:.6f} seconds ".format(end-start))

mydb.commit()
cursor.close()
