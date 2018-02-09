import pandas as pd

weekly_cc = pd.read_csv("malaria_cases_weekly.csv")

cc_by_month = weekly_cc.groupby(['yr', 'mon'])

ref_cc = {}
for (year, month), cc_per_week in cc_by_month:
    print(year)
    print(month)
    print(cc_per_week)
    print(cc_per_week['mal_cc'].sum())
    ref_cc[str(year) + "_" + str(int(month))] = cc_per_week['mal_cc'].sum()

print(ref_cc)
pd.DataFrame.from_dict(ref_cc,  orient = "index").to_csv("cc_ref_data.csv")

