# -*- coding: utf-8 -*-
"""
Created on Thu Mar 30 17:24:07 2023

@author: cta4r

This is the program to visualize 

"""


import math
import numpy as np
import pandas as pd
import streamlit as st

from datetime import datetime

from pykeri.scidata.matprop import MatProp
# from pykeri.thermoelectrics.TEProp import TEProp
from pykeri.thermoelectrics.TEProp_xls import TEProp as TEProp_xls
from pykeri.thermoelectrics.TEProp_df import TEProp as TEProp_df
from pykeri.thermoelectrics.solver1d.leg import Leg
from pykeri.thermoelectrics.solver1d.environment import Environment
from pykeri.thermoelectrics.solver1d.device import Device

from pykeri.byungkiryu import byungkiryu_util as br

from library.tematdb_util import get_Ts_TEPZT
from library.tematdb_util import draw_mat_teps, tep_generator_from_excel_files
from library.draw_ZT_errors_with_mat import draw_mat_ZT_errors
from library.dev_performance import set_singleleg_device, run_pykeri, draw_dev_perf

formattedDate, yyyymmdd, HHMMSS = br.now_string()


st.title("teMatDb (ver1.1.0)")
st.subheader(":blue[t]hermo:blue[e]lectric :blue[Mat]erial :blue[D]ata:blue[b]ase")
st.markdown("- High quality thermoelectric (TE) database (DB).")
# st.markdown("- Suitable for _transport mechanism_ analysis & _machine learning_ .")
# st.markdown("- Status: :red[teMatDb ver1.1.0]. Developed by BR @ KER.")
# st.markdown("- Open :red[Left Sidebar] to choose DB and Mat.")


tab1a, tab1b, tab1c, tab2, tab3, tab4 = st.tabs(["ThermoElectric Material", 
                                                 "Database quality", 
                                                 "Efficiency", "Theory", "Link", "Contact"])


###############
###############
###############
## Sidebar, choose DB, choose mat
with st.sidebar:
    st.subheader(":red[Select TE Mat. DB]")
    options =['teMatDb','teMatDb_expt','Starrydata2 (not work yet)']
    db_mode = st.radio( 'Select :red[Thermoelectric DB] :',
        options=options, index=0,
        label_visibility="collapsed")    
    
    if (db_mode == 'teMatDb'):
        file_tematdb_metadata_csv = "_tematdb_metadata_v1.1.0-20230412_brjcsjp.xlsx"
        file_tematdb_db_csv       =  "tematdb_v1.1.0_completeTEPset.csv"
        
        df_db_meta = pd.read_excel("./"+file_tematdb_metadata_csv, sheet_name='list', )
        df_db_csv = pd.read_csv("./data_csv/"+file_tematdb_db_csv)
        
        file_tematdb_error_csv = "error.csv"
        df_db_error0 = pd.read_csv("./data_error_analysis/"+file_tematdb_error_csv)
        err_cols = ['sampleid','JOURNAL', 'YEAR', 
               'Corresponding_author_main', 'Corresponding_author_institute',
               'Corresponding_author_email', 'figure_number_of_targetZT',
               'label_of_targetZT_in_figure', 'figure_label_description',]
        df_db_error = pd.merge( df_db_error0, df_db_meta[err_cols], on='sampleid', how='left')
        
    else:
        pass
      
    ## choose sampleid
    st.subheader(":red[Select sampleid]")
    option_sampleid = list(df_db_meta.sampleid.unique())
    sampleid = st.selectbox('Select or type sampleid:',
        option_sampleid, index=0,
        label_visibility="collapsed")   
    
    df_db_meta_sampleid = df_db_meta[ df_db_meta.sampleid == sampleid]
    doi = df_db_meta_sampleid.DOI.iloc[0]
    link_doi = '[DOI: {}](http://www.doi.org/{})'.format(doi,doi)
    st.markdown(link_doi, unsafe_allow_html=True)
    corrauthor = df_db_meta_sampleid.Corresponding_author_main.iloc[0]
    corremail  = df_db_meta_sampleid.Corresponding_author_email.iloc[0] 
    st.markdown("Correspondence: {}  \n(email: {})".format(corrauthor, corremail)) 
    
    interp_opt = {MatProp.OPT_INTERP:MatProp.INTERP_LINEAR,\
                  MatProp.OPT_EXTEND_LEFT_TO:1,          # ok to 0 Kelvin
                  MatProp.OPT_EXTEND_RIGHT_BY:2000}        # ok to +50 Kelvin from the raw data
    TF_mat_complete, mat = tep_generator_from_excel_files(sampleid, interp_opt)
    # df_db_csv_sampleid = df_db_csv[ df_db_csv.sampleid == sampleid]
    # df_alpha = df_db_csv_sampleid[ df_db_csv_sampleid.tepname == 'alpha']
    # df_rho   = df_db_csv_sampleid[ df_db_csv_sampleid.tepname == 'rho'  ]
    # df_kappa = df_db_csv_sampleid[ df_db_csv_sampleid.tepname == 'kappa']
    # df_ZT    = df_db_csv_sampleid[ df_db_csv_sampleid.tepname == 'ZT'   ]
    # try:
    #     mat = TEProp_df.load_from_df(df_alpha, df_rho, df_kappa, df_ZT, mat_name='test')
    #     mat.set_interp_opt(interp_opt)
    #     TF_mat_complete = True
    # except:
    #     TF_mat_complete = False
        

    label_db = "DB: {}".format(db_mode)
    label_sampleid = "sampleid: {}".format(sampleid)
    label_doi = '[DOI: {}]'.format(doi)    


###############
###############
###############
## Material data for given sampleid
with tab1a:  
    ## Read mat, TEP
    # st.header("[db_mode  = :blue[{}]]".format(db_mode) )
    st.header(":blue[I. DB MetaData Table]")
    with st.expander("See material metadata:", expanded=True):
        st.write(df_db_meta)                

    st.header(":blue[II. Material Data] ")
    st.subheader(":red[[db_mode  = :blue[{}]]]".format(db_mode) + ":red[[sampleid = :blue[{}]]]".format( sampleid))
    
    st.subheader(":red[Material Summary]")
    st.markdown(link_doi, unsafe_allow_html=True)
    
    colnames = ['sampleid', 'DOI', 'JOURNAL', 'YEAR',
                'GROUP', 'BASEMAT','Composition_by_element', 'Composition_detailed',
                'mat_dimension(bulk, film, 1D, 2D)', 'SC/PC', 'Reaction', 'Milling',
                'SINTERING', 'PostProcessing']
    for colname in colnames:
        st.markdown("{}: :blue[{}]".format(colname, df_db_meta_sampleid[colname].iloc[0]))
    
    st.subheader(":red[Material Information]")
    st.write(df_db_meta_sampleid)

 
    ## print material(mat) tep
    st.subheader(":red[Transport Properties] (Table)")
    df_db_csv_sampleid = df_db_csv[ df_db_csv.sampleid == sampleid]
    if not TF_mat_complete:
        st.write(':red[TEP is invalid because TEP set is incomplete..]')    
    if TF_mat_complete:
        with st.expander("See rawdata of material TEPs:"):
            st.write(df_db_csv_sampleid)
    
    ## draw material(mat) tep
    st.subheader(":red[Transport Properties] (interpolated) (Figure)")
    if not TF_mat_complete:
        st.write(':red[TEP is invalid because TEP set is incomplete..]')    
    if TF_mat_complete:        
        fig1, fig2 = draw_mat_teps(mat, 
                                   label_db=label_db, 
                                   label_sampleid=label_sampleid, 
                                   label_doi=label_doi
                                   )
        with st.expander("See TEP curves:", expanded=True):        
            st.pyplot(fig1)   
            st.caption("Figure. Thermoelectric Properties of :blue[sampleid={}] in :blue[{}].".format(sampleid,db_mode))
        with st.expander("See rho, PF, RK, Loenz curves:", expanded=True):        
            st.pyplot(fig2)        
            st.caption("Figure. Extended Thermoelectric Properties of :blue[sampleid={}] in :blue[{}].".format(sampleid,db_mode))
        with st.expander("See Interpolation schemes:", expanded=False):  
            ZT_raw   = np.array( mat.ZT.raw_data() ).T
            autoTc = mat.min_raw_T
            autoTh = mat.max_raw_T    
            TcZT = min(ZT_raw[0])
            ThZT = max(ZT_raw[0])    
            TcTEPZT = max(autoTc, TcZT,1)
            ThTEPZT = min(autoTh, ThZT)            
            st.markdown(":blue[TEP interpolation interval (Tc, Th) = ({:6.2f} K, {:6.2f} K)]  \n".format(autoTc,autoTh) \
                        + ":red[ZT interpolation interval (Tc, Th) = ({:6.2f} K, {:6.2f} K)]  \n".format(TcZT,ThZT) \
                        + ":green[Union of TEP and ZT interpolation interval (Tc, Th) = ({:6.2f} K, {:6.2f} K)]".format(TcZT,ThZT))

        
    ## Digitized data quality using error analysis
    st.header(":blue[III. ZT Self-consistency Analyzer]")
    st.subheader(":red[[db_mode  = :blue[{}]]]".format(db_mode) + ":red[[sampleid = :blue[{}]]]".format( sampleid))
    st.subheader(":red[Material Error (or Noise) Statistics]")
    if not TF_mat_complete:
        st.write(':red[TEP is invalid because TEP set is incomplete..]')    
    if TF_mat_complete:   
        try:
            # file_tematdb_error_csv = "error_20230407_231304.csv"
            df_db_error_sampleid = df_db_error[ df_db_error.sampleid == sampleid]
        except:
            st.markdown('Yet, no error reports')
        else:            
            st.write(df_db_error_sampleid)
            
            if ( np.abs( df_db_error_sampleid.dpeakZT.iloc[0] ) > 0.1 ):
                st.markdown("**:red[Warning: peak ZT mismatch is larger than 0.1]**")
            else:
                st.markdown("**:blue[Self-consistent: peak ZT mismatch is smaller than, 0.1]**")
            st.markdown(":black[Author peak ZT (searched from published ZT data): peak-ZT raw = {:6.2f}]".format(df_db_error_sampleid.peakZT_raw_on_Ts_ZT.iloc[0]))
            st.markdown(":black[Re-evaulated peak ZT (calculated from interpolated TEPs): peak-ZT TEP = {:6.2f}]".format(df_db_error_sampleid.peakZT_TEP_on_Ts_TEP.iloc[0])) 
                
            if ( np.abs( df_db_error_sampleid.davgZT.iloc[0] ) > 0.1 ):
                st.markdown("**:red[Warning: average ZT mismatch is larger than 0.1]**")
            else:
                st.markdown("**:blue[Self-consistent: average ZT mismatch is smaller than, 0.1]**")
            st.markdown(":black[Author avg ZT (calculated from interpolated ZTs): avg ZT raw = {:6.2f}]".format(df_db_error_sampleid.avgZT_raw_on_Ts_ZT.iloc[0]))
            st.markdown(":black[Re-evaulated avg ZT reevaulated (caculated from interpolated TEPs): avg ZT TEP = {:6.2f}]".format(df_db_error_sampleid.avgZT_TEP_on_Ts_TEP.iloc[0])) 
        
            with st.expander("How to calculateSee Lp errors and etc...:", expanded=False):        
                st.markdown(":red[error was calculated blah blbah using following equations (to be filled later)]")
                
            fig3 = draw_mat_ZT_errors(mat, label_db=label_db, label_sampleid=label_sampleid, label_doi=label_doi)
            st.pyplot(fig3)        
            st.caption("Figure. ZT error analysis of :blue[sampleid={}] in :blue[{}].".format(sampleid,db_mode))
            
            
            
        
# with tab1c:  
    st.header(":blue[IV. Material Performance]")
    st.subheader(":red[[db_mode  = :blue[{}]]]".format(db_mode) + ":red[[sampleid = :blue[{}]]]".format( sampleid))
    if not TF_mat_complete:
        st.write(':red[TEP is invalid because TEP set is incomplete..]')    
    if TF_mat_complete:
        # st.write(':blue[TEP is valid..]')     
        
        # autoTc, autoTh = float(mat.min_raw_T), float(mat.max_raw_T)
        limitTc = float( math.floor(autoTc/50)*50.0 )
        limitTh = float( math.ceil(autoTh/50)*50.0 )
        
        st.markdown(":blue[TEP interpolation:] piecewise-linear manner.  \n "
                    +":blue[TEP extrapolation:] constant-extrapolated.  \n "    
                    +":blue[TEP interpolation at the interval (Tc, Th) = ({:6.2f} K, {:6.2f} K)]".format(autoTc,autoTh))
        
        
        st.subheader(":red[Singleleg Device Spec.]")
        with st.form("my_form"):
            st.write("Valid temperature range considering Ts of TEPs: Tc > {:6.2f} K, Th < {:6.2f} K".format(autoTc, autoTh))
            
            col1, col2 = st.columns([2,2])
            with col1:
                Tc = st.number_input(r'$T_c$: cold side temperature in [K]',
                                min_value = limitTc, max_value = limitTh, step = 25.0,
                                value = limitTc+25 )
                Th = st.number_input(r'$T_h$: hot side temperature in [K]',
                                min_value = limitTc, max_value = limitTh, step = 25.0,
                                value = limitTh-25 )
            with col2:
                leg_length_in_mm = st.number_input('leg_length in mm',
                                                     min_value = 0.5, max_value = 10.0, step = 0.5,
                                                     value = 3.0)
                leg_area_in_mmsq = st.number_input('leg_area in mm x mm',
                                                     min_value = 0.25, max_value = 25.0, step = 1.0,
                                                     value = 9.0)
                N_leg = st.number_input('number of legs',
                                                      min_value = 1, max_value = 1, step = 1,
                                                      value = 1, disabled=True)
            
            submitted = st.form_submit_button("Calculate Material Performance (singleleg device).")
            if submitted:                   
                leg_length = leg_length_in_mm *1e-3
                leg_area   = leg_area_in_mmsq *1e-6
                N_leg      = 1  
            else:
                leg_length = 3 *1e-3
                leg_area   = 9 *1e-6
                N_leg      = 1 

        dev = set_singleleg_device(mat, leg_length,leg_area,N_leg,Th,Tc)            
        # dev = set_singleleg_device(df_db_csv,sampleid,leg_length,leg_area,N_leg,Th,Tc)
        df_dev_run_currents_result, df_dev_run_powMax_result, df_dev_run_etaOpt_result = run_pykeri(dev, sampleid,leg_length,leg_area,N_leg,Th,Tc)
        fig4 = draw_dev_perf(df_dev_run_currents_result, df_dev_run_powMax_result, df_dev_run_etaOpt_result)
        st.pyplot(fig4)
        with st.expander("See Material performance curves:", expanded=True):        
            st.write("currents performances")
            st.write(df_dev_run_currents_result)
            st.write("Power max performances")
            st.write(df_dev_run_powMax_result)
            st.write("Optimal efficiency performances")
            st.write(df_dev_run_etaOpt_result)
            
###############
###############
###############
## DB Stat
with tab1b:       
    st.header(":blue[DataFrame for Error Table]")
    st.write(df_db_error)
    
    
    cri_cols = [
                'davgZT',
                'dpeakZT',
                'Linf',
                ]
    cri_vals = [
                0.10,
                0.10,
                0.10,
                ]
    
    df_db_error_criteria_list = []
    esampleid_list_df_db_error_eriteria = []
    for cri_col, cri_val in zip(cri_cols, cri_vals):   
        error_criteria = np.abs( df_db_error[cri_col] > cri_val )
        df_db_error_criteria = df_db_error[ error_criteria ].copy()
        df_db_error_criteria.sort_values(by=cri_col,ascending=False, inplace=True)
        # df_db_error_criteria.reset_index(inplace=True, drop=True)
        df_db_error_criteria.set_index('sampleid', inplace=True, drop=False)
        # df_db_error_criteria.drop(columns='index',inplace=True)
        # df_db_error_criteria1 = df_db_error_criteria    
        
        cri_str = ":blue[Noisy samples: {} > {}]".format(cri_col, cri_val)
        st.header(cri_str)
        # st.header(":red[Noisy samples: {} > {}]".format(cri_col, cri_val))  
        st.markdown("There are :red[{}] noisy-cases.".format(len(df_db_error_criteria)) )
        st.write(df_db_error_criteria)
        df_db_error_criteria_list.append(df_db_error_criteria)
        sampleid_list = df_db_error_criteria.sampleid.unique().tolist()
        st.write(sampleid_list)
        # esampleid_list_df_db_error_eriteria = esampleid_list_df_db_error_eriteria + sampleid_list
        del df_db_error_criteria
        # del 
    
    # st.header(":red[Noisy samples: Linf > 0.15]")
    # error_criteria = error_criteria1
    # df_db_error_criteria = df_db_error[ error_criteria1 ].copy()
    # df_db_error_criteria.sort_values(by='Linf',ascending=False, inplace=True)
    # df_db_error_criteria.reset_index(inplace=True)
    # df_db_error_criteria1 = df_db_error_criteria    
    # st.write(df_db_error_criteria1)

    # st.header(":red[Noisy samples: Linf > 0.15]")
    # error_criteria = error_criteria1
    # df_db_error_criteria = df_db_error[ error_criteria1 ].copy()
    # df_db_error_criteria.sort_values(by='Linf',ascending=False, inplace=True)
    # df_db_error_criteria.reset_index(inplace=True)
    # df_db_error_criteria1 = df_db_error_criteria    
    # st.write(df_db_error_criteria1)
    
    
    # sampleids_error_criteria2 = df_db_error[ error_criteria1 ].sampleid.unique()
    # st.write(sampleids_error_criteria1)
    
    # sampleids_error_criteria3 = df_db_error[ error_criteria1 ].sampleid.unique()
    # st.write(sampleids_error_criteria1)
    
    
    # if not TF_mat_complete:
    #     st.write(':red[TEP is invalid because TEP set is incomplete..]')    
    # if TF_mat_complete:   
    # try:
    #     # file_tematdb_error_csv = "error_20230407_231304.csv"
    #     file_tematdb_error_csv = "error.csv"
    #     df_db_error = pd.read_csv("./data_error_analysis/"+file_tematdb_error_csv)
    #     # df_db_error_sampleid = df_db_error[ df_db_error.sampleid == sampleid]
    # except:
    #     st.markdown('Yet, no error reports')
    # else:            
    #     st.write(df_db_error)
        

    
    
    
with tab1c:  
    st.header(":red[tab1c to be made]")  
        # st.write(dev.report())

with tab2:
    st.header(":blue[Data sources]")
    st.header(":blue[Figures]")
    st.header(":blue[Efficiency calculation]")
    st.header(":blue[References]")
    # st.markdown("[1] Chung, Jaywan, and Byungki Ryu. “Nonlocal Problems Arising in Thermoelectrics.” Mathematical Problems in Engineering 2014 (December 15, 2014): e909078. https://doi.org/10.1155/2014/909078.")
    st.markdown("[1] Ryu, Byungki, Jaywan Chung, Eun-Ae Choi, Pawel Ziolkowski, Eckhard Müller, and SuDong Park. “Counterintuitive Example on Relation between ZT and Thermoelectric Efficiency.” Applied Physics Letters 116, no. 19 (May 13, 2020): 193903. https://doi.org/10.1063/5.0003749.")
    st.markdown("[2] Chung, Jaywan, Byungki Ryu, and SuDong Park. “Dimension Reduction of Thermoelectric Properties Using Barycentric Polynomial Interpolation at Chebyshev Nodes.” Scientific Reports 10, no. 1 (August 10, 2020): 13456. https://doi.org/10.1038/s41598-020-70320-7.")
    st.markdown("[3] Ryu, Byungki, Jaywan Chung, and SuDong Park. “Thermoelectric Degrees of Freedom Determining Thermoelectric Efficiency.” iScience 24, no. 9 (September 24, 2021): 102934. https://doi.org/10.1016/j.isci.2021.102934.")
    st.markdown("[4] Chung, Jaywan, Byungki Ryu, and Hyowon Seo. “Unique Temperature Distribution and Explicit Efficiency Formula for One-Dimensional Thermoelectric Generators under Constant Seebeck Coefficients.” Nonlinear Analysis: Real World Applications 68 (December 1, 2022): 103649. https://doi.org/10.1016/j.nonrwa.2022.103649.")
    st.markdown("[5] Ryu, Byungki, Jaywan Chung, Masaya Kumagai, Tomoya Mato, Yuki Ando, Sakiko Gunji, Atsumi Tanaka, et al. “Best Thermoelectric Efficiency of Ever-Explored Materials.” iScience 26, no. 4 (April 21, 2023): 106494. https://doi.org/10.1016/j.isci.2023.106494.")
    st.write("(Style: Chicago Manual of Style 17th edition (full note))")

with tab3:
    st.subheader("Thermoelectric Power Generator Web Simulator Lite ver.0.53a")
    st.write(":blue[https://tes.keri.re.kr/]")
    
    st.subheader("Korea Electrotechnology Research Institute (KERI)")
    st.write(":blue[https://www.keri.re.kr/]")
   
    st.subheader("Alloy Design DB (v0.33)")
    st.write(":blue[https://byungkiryu-alloydesigndb-demo-v0-33-main-v0-33-u86ejf.streamlit.app/]")
    

with tab4:
   
    st.header(":blue[KERI Thermoelectric Science TEAM]")
    with st.expander("See Members:", expanded=False):   
        st.subheader("SuDong Park, Dr. (박수동)")
        st.subheader("Byungki Ryu, Dr. (류병기)")
        st.markdown("byungkiryu at keri.re.kr")
        st.subheader("Jaywan Chung, Dr. (정재환)")
        st.subheader("Jongho Park, Mr. (박종호)")
        st.subheader("Ji-Hee Son, Ms. (손지희)")
        st.subheader("Jeongin Jang, Miss (장정인)")
        st.subheader("Sungjin Park, Dr. (박성진)")
    
    st.header(":blue[Visit KERI. How to Come?]")
    with st.expander("See Maps:", expanded=False):        
        st.markdown("")
        st.image("./image/southkorea_map_screenshot.png")    
        st.caption("(South Korea Map) Changwon-si")
        st.image("./image/changwon_map_screenshot.png")    
        st.caption("(Changwon Map) Korea Electrotechnology Research Institute (KERI)")
        st.image("./image/map_2023.jpg")   
        st.caption("(KERI map) Office and Lab, building #3 and #5")
    
    st.header(":blue[QR Code]")
    with st.expander("See QR code (v1.0.1):", expanded=False):            
        st.image("./image/"+"qrcode_tematdb-v1-0-0-main-v1-0-1-abc.streamlit.app.png")
        # st.header("https://qrco.de/bds6GG/")
    with st.expander("See QR code (v1.0.0):", expanded=False):            
        st.image("./image/"+"qrcode_tematdb-v1-0-0-main-v1-0-0-abc.streamlit.app.png")
        # st.header("https://qrco.de/bds6GG/")
        
        
    # st.image("Where is Changwon")