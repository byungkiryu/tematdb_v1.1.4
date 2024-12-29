# -*- coding: utf-8 -*-
"""
Created on Fri Mar 18 15:32:28 2022

@author: byungkiryu

This code read excel files which contatin raw-digitized things
 into a single merged csv file.

"""

import os
from datetime import datetime
from pykeri.thermoelectrics.TEProp_xls import TEProp
import pandas as pd
from pykeri.byungkiryu import byungkiryu_util as br

formattedDate, yyyymmdd, HHMMSS = br.now_string()


# DIR_tematdb = 'R:/old OneD  2021 1223/10-ResMAIN/00-RES/11-etaMap/00 keri db/100-teMatDb/teMatDb/1-문헌_0손박임/210824 SnSe 3.1/'
# DIR_tematdb = './210824 SnSe 3.1/'
# DIR_tematdb = './tematdb v10.00 20220418 tep check brjcsjp/'
version = "v1.1.0"
DIR_tematdb = "./tematdb_excels/"
DIR_tematdb = "./data_excel/"

fileseq = 1
idx_ini = 1  + (fileseq-1)*50
idx_fin = 50 + (fileseq-1)*50


# filename1 = "_tematdb_tep_excel_{:s}_{:05d}-{:05d}_confirmed_220606.xlsx".format(version,1,50)
# filename2 = "_tematdb_tep_excel_{:s}_{:05d}-{:05d}_confirmed_220606.xlsx".format(version,51,100)
# filename3 = "_tematdb_tep_excel_{:s}_{:05d}-{:05d}_confirmed_220606.xlsx".format(version,101,150)
# filename4 = "_tematdb_tep_excel_{:s}_{:05d}-{:05d}_confirmed_220606.xlsx".format(version,151,200)
# filename5 = "_tematdb_tep_excel_{:s}_{:05d}-{:05d}_confirmed_220606.xlsx".format(version,201,250)
# filename6 = "_tematdb_tep_excel_{:s}_{:05d}-{:05d}_confirmed_220606.xlsx".format(version,251,300)
# filename7 = "_tematdb_tep_excel_{:s}_{:05d}-{:05d}_confirmed_220606.xlsx".format(version,301,350)
# filename8 = "_tematdb_tep_excel_{:s}_{:05d}-{:05d}_confirmed_220606.xlsx".format(version,351,400)
# filename9 = "_tematdb_tep_excel_{:s}_{:05d}-{:05d}_confirmed_220606.xlsx".format(version,401,450)
# files = [filename1, filename2, filename3, filename4, filename5, filename6,
#          filename7, filename8, filename9 ]
files = os.listdir('./data_excel/')

sampleid_ini, sampleid_fin = 1, 4
# sampleid_ini, sampleid_fin = 291, 310
# sampleid_ini, sampleid_fin = 1, 350
sampleid_ini, sampleid_fin = 1, 450
df_raw_tep_list = []

sampleid_list = list(range(sampleid_ini,sampleid_fin+1))
# sampleid_list = sampleid_list[0:4]
for sampleid in sampleid_list:
    # idx = sampleid
    fileindex = int((sampleid-1)/50)
    filename = files[fileindex]
    sheetname = "#{:05d}".format(sampleid)
    

    try:
        mat = TEProp.from_dict({'xls_filename': DIR_tematdb+filename,
                                'sheetname': sheetname, 'color': (sampleid/255, 0/255, 0/255)} )
        autoTc = mat.min_raw_T
        autoTh = mat.max_raw_T
    except:
        print(filename, sampleid, 'data set is incompelete or empty')
        continue
    
    df_tep_each = pd.DataFrame()
    df_alpha_each = pd.DataFrame(mat.Seebeck.raw_data(), columns=['Temperature','tepvalue'] )
    df_alpha_each['tepname'] = 'alpha'
    df_alpha_each['unit'] = '[V/K]'
    
    df_rho_each = pd.DataFrame(mat.elec_resi.raw_data(), columns=['Temperature','tepvalue'] )
    df_rho_each['tepname'] = 'rho'
    df_rho_each['unit'] = '[Ohm-m]'
    
    df_kappa_each = pd.DataFrame(mat.thrm_cond.raw_data(), columns=['Temperature','tepvalue'] )
    df_kappa_each['tepname'] = 'kappa'
    df_kappa_each['unit'] = '[W/m/K]'
    
    df_ZT_each = pd.DataFrame(mat.ZT.raw_data(), columns=['Temperature','tepvalue'] )
    df_ZT_each['tepname'] = 'ZT'
    df_ZT_each['unit'] = '[1]'
    
    df_tep_each = pd.concat([df_alpha_each, df_rho_each, df_kappa_each, df_ZT_each])
    df_tep_each['sampleid'] = sampleid
    df_tep_each['autoTc'] = autoTc
    df_tep_each['autoTh'] = autoTh
    
    df_raw_tep_list.append( df_tep_each.copy() )
    
    
    len_alpha = len(df_alpha_each)
    len_rho   = len(df_rho_each)
    len_kappa = len(df_kappa_each)
    len_ZT    = len(df_ZT_each)
    len_tep   = len(df_tep_each)
    # del(df_tep_each)
    
    print(filename, sheetname, " data lenghs of alpha/rho/kappa/ZT/all=",
          len_alpha, len_rho, len_kappa, len_ZT, len_tep)


dbname = 'tematdb'
versionshort  = 'tematdb_{:s}_completeTEPset'.format(version)
versionprefix = 'tematdb_{:s}_completeTEPset_convertedOn_{}_'.format(version,formattedDate)

df_tep_raw = pd.concat( df_raw_tep_list, copy=True,ignore_index=True)
datetimeupdate =  datetime.now()

df_tep_all = df_tep_raw[['sampleid','tepname','Temperature','tepvalue','unit','autoTc','autoTh']].copy()
sampleid_min = df_tep_all.sampleid.min()
sampleid_max = df_tep_all.sampleid.max()

versiontype ="range"
versionlabel = versionprefix+'_{:s}_{:d}_to_{:d}'.format(versiontype,sampleid_min, sampleid_max)

# df_tep_all['id_tematdb'] = df_tep_all.sampleid.copy()
df_tep_all['dbname']  = dbname
df_tep_all['version'] = version
df_tep_all['versionlabel'] = versionlabel
df_tep_all['update']  = datetimeupdate
df_tep_all['pykeri_compatible'] = True
df_tep_all.to_csv( "./data_csv/"+versionlabel+'.csv',index=False )
df_tep_all.to_csv( "./data_csv/"+versionshort+'.csv',index=False )


