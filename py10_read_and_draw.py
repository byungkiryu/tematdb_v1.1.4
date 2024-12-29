# -*- coding: utf-8 -*-
"""
Created on Thu Mar 30 17:24:07 2023

@author: cta4r

This is the program to visualize 

"""



import numpy as np
import pandas as pd
# import streamlit as st

from datetime import datetime

from pykeri.scidata.matprop import MatProp
from pykeri.thermoelectrics.TEProp import TEProp
from pykeri.thermoelectrics.TEProp_xls import TEProp as TEProp_xls
from pykeri.thermoelectrics.solver1d.leg import Leg
from pykeri.thermoelectrics.solver1d.environment import Environment
from pykeri.thermoelectrics.solver1d.device import Device

from pykeri.byungkiryu import byungkiryu_util as br
from library.tematdb_util import draw_mat_teps, tep_generator_from_excel_files


# formattedDate, yyyymmdd, HHMMSS = br.now_string()



## choose DB
db_mode = 'teMatDb'
df_db_meta = pd.read_excel("./"+"_tematdb_metadata_v1.00_0-20230327_brjcsjp.xlsx", sheet_name='list', )
sampleid = 1
df_db_meta_sampleid = df_db_meta[ df_db_meta.sampleid == sampleid]

doi = df_db_meta_sampleid.DOI.iloc[0]
link_doi = '[DOI: {}] (http://www.doi.org/{})'.format(doi,doi)

print("sampleid= ",sampleid)
print("doi=      ",doi)
print(link_doi)

## Read mat, TEP

interp_opt = {MatProp.OPT_INTERP:MatProp.INTERP_LINEAR,\
          MatProp.OPT_EXTEND_LEFT_TO:1,          # ok to 0 Kelvin
          MatProp.OPT_EXTEND_RIGHT_BY:2000}        # ok to +50 Kelvin from the raw data
TF_mat_complete, mat = tep_generator_from_excel_files(sampleid, interp_opt)
print(df_db_meta_sampleid)

## print mat tep
df_db_csv = pd.read_csv("./data_csv/"+"tematdb_v1.00_completeTEPset_convertedOn_20230331_014335__range_1_to_424.csv")
df_db_csv_sampleid = df_db_csv[ df_db_csv.sampleid == sampleid]
if not TF_mat_complete:
    print(':red[TEP is invalid because TEP set is incomplete..]')    
if TF_mat_complete:
    print(df_db_csv_sampleid)


label_db = "DB: {}".format(db_mode)
label_sampleid = "sampleid: {}".format(sampleid)
label_doi = '[DOI: {}]'.format(doi)  
# fig1, fig2 = draw_mat_teps(mat)
fig1, fig2 = draw_mat_teps(mat, 
                           label_db=label_db, 
                           label_sampleid=label_sampleid, 
                           label_doi=label_doi
                           )

