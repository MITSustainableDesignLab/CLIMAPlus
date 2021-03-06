from flask import Flask, jsonify, session, g
from flask import render_template, request, url_for, redirect, make_response
#from flask.ext.session import Session
import csv, json
import sys, os
import data_climates as ddc
import CPlus_Climate as cc
import climabox as cb
import time
import shutil

app = Flask(__name__)
app.secret_key = '3Z\x15\xfd"\x0e#\x1c}\x8er\xbc<\x16\xf1\xbe\xb6\x83/\x00]\tfP'

# "db":self.Tdb, "dp":self.Tdp, "rh":self.RHout, "bp":self.BP, 
# "radg":self.RadGlobal, "radn":self.RadNormal, 
# "radd":self.RadDif, "wd":self.windDir, "wv":self.windVel

@app.route('/', methods=['GET', 'POST'])
def index():
    try: 
        ff = str(session['id'])  
    except KeyError:
        ff = '1234'
    session['location'] = ''
    session['city'] = ''
    session['id'] = time.time()
    
    # return render_template("ClimateSelect.html")

    resp = make_response(render_template('ClimateSelect.html'))
    resp.set_cookie('cookie', ff)

    return resp

@app.route('/ClimateSelect', methods=['GET', 'POST'])
def ClimateSelect():
    return render_template("ClimateSelect.html")

@app.route('/ClimateInfo', methods=['GET', 'POST'])
def ClimateInfo():
    if request.method == 'POST':
        ff = str(session['id'])
        wthdata = {}
        if 'selectEPW' in request.form:
            city = (request.form['city'])
            _loc = ddc.findEPWN(str(city))
            location = _loc.fileEPW
            session['locationJs'] = './static/json/'+_loc.fileEPW+'.json'
            session['locationJsPsy'] = './static/json/'+_loc.fileEPW+'.json'
            
            session['location'] = location
            session['city'] = city

    return render_template("ClimateInfo.html")

@app.errorhandler(Exception)
def handle_error(error):
    return render_template("ClimateSelect.html")

# a simple sunpath diagram
@app.route('/SolarP', methods=['GET','POST'])
def SolarP():
    ff = str(session['id'])
    # with open('static/'+ff+'.json') as wthj:
    with open(session['locationJs']) as wthj:
        wth = json.load(wthj)
    # print ("+++++++++++++++test json",wth["psych_wth"])
    lat, lon, tz = round((float(wth['latitude'])),0), round((float(wth["longitude"]))*-1,0), round((float(wth["timezone"]))*-15,0)
    rf = cc.radFacade(lat,lon,wth['radn'], wth['radd'],wth['radg'])
    
    ###Facade radiation
    session['HORRADM'] = rf.horradM
    session['RADMS'] = rf.radMS
    session['RADME'] = rf.radME
    session['RADMW'] = rf.radMW
    session['RADMN'] = rf.radMN

    # print('++++++++++++++++',rf.radMN)

    ###Sunpath diagram
    sp = cc.sunPath(rf)
    analemma = sp.analemma
    monthLines = {1:sp.june, 2:sp.dec, 3:sp.mar}
    monthLines_ = {4:sp.june_, 5:sp.mar_, 6:sp.dec_,}
 
    ###CummRad multiple process
    ###Cummulative radiation, runs the radmap script
    # ff = str(session['id'])
    # os.system('mkdir '+ff)

    # radLib = ['CreateRadiationMap.sh','CreateRadiationMap_t.sh','gencumulativesky','oconv','Alpha_gcsky.rad','Alpha.rad','rpict','rayinit.cal','falsecolor2.py','helvet.fnt','ra_tiff']
    # for lib in radLib:
    #     shutil.copy('RadSim_Main/'+lib,ff)
    # print(ff)
    # ddc.runCumRad(ff)
    # shutil.rmtree('ff')

    city__ = (session['city'])
    # city_ = city__.replace(" ","")
    cityL = city__.split(' (')
    maxRad = ddc.findMaxRad(str(cityL[0]))
    session['maxRad'] = maxRad.maxRad

    # print('**********SOLAR******', session['location'], session['city'], maxRad.maxRad)

    return render_template("SolarP.html", analemma = analemma, monthLines = monthLines, monthLines_ = monthLines_)

# this is just to run radiation map simulations with a unique html link. can't be 
# accessed directly from climaplus
@app.route('/runRADSim', methods=['GET','POST'])
def runRADSim():
    tempRad = str(session['id'])
    os.system('mkdir '+tempRad)
    ###Cummulative radiation, runs the radmap script
    radLib = ['CreateRadiationMap.sh','CreateRadiationMap_t.sh','gencumulativesky','oconv','Alpha_gcsky.rad','Alpha.rad','rpict','rayinit.cal','falsecolor2.py','helvet.fnt','ra_tiff']
    for lib in radLib:
        shutil.copy('RadSim_Main/'+lib,tempRad)
    ddc.runCumRad(tempRad)
    shutil.rmtree(tempRad)

    return render_template("runRADSim.html")

# Monthly avertage temperature
@app.route('/TempRH', methods=['GET', 'POST'])
def TempRH():

    ff = str(session['id'])
    # with open('static/'+ff+'.json') as wthj:
    with open(session['locationJs']) as wthj:
        wth = json.load(wthj)

    dd = cc.degreeDays(wth['db'],18,10) 
    cz_ = cc.CZdef(dd)
    cz = cz_.CZ[2]
    session['CZ'] = int(cz)

    monthlyData = cc.monthlyData(wth['db'])
    data = {'mean': monthlyData.hourlyMean, 'min': monthlyData.hourlyMin, 'max': monthlyData.hourlyMax}
    data_ = {'db':wth['db'], 'rh':wth['rh'], 'bp':wth['bp']}
    sp = {'tupper':24, 'tlower':18, 'setHDD':18, 'setCDD':10}
    dd_data = {'HDD':int(dd.HDD), 'CDD':int(dd.CDD), 'HDDL':dd.HDDL, 'CDDL':dd.CDDL}

    if request.method == 'POST':
        
        if 'submitTemp' in request.form:
            ### Temperature
            tupper = request.form['tupper']
            tlower  = request.form['tlower']

            if tupper != "": sp['tupper'] = tupper  
            else: tupper = sp['tupper']
            if tlower != "": sp['tlower'] = tlower 
            else: tlower = sp['tlower']

            # print ("tupper", tupper, tlower, sp['tupper'], sp['tlower'])

        elif 'submitDD' in request.form:
            ### Heating and cooling degree days
            HDDsp = (request.form['hddsp']) 
            CDDsp = (request.form['cddsp'])
            if HDDsp is None: HDDsp = 18  
            elif HDDsp != "": HDDsp = round(float(HDDsp),1)
            else: HDDsp = sp['setHDD']
            
            if CDDsp is None: CDDsp = 10  
            elif CDDsp != "": CDDsp = round(float(CDDsp),1)
            else: CDDsp = sp['setCDD']

            dd = cc.degreeDays(wth['db'],HDDsp,CDDsp)

            dd_data['HDD'] = int(dd.HDD)
            dd_data['CDD'] = int(dd.CDD)
            dd_data['HDDL'] = dd.HDDL
            dd_data['CDDL'] = dd.CDDL
            sp['setHDD'], sp['setCDD'] = HDDsp, CDDsp

        # return redirect(request.referrer)

    return render_template("TempRH.html", data= data, sp=sp, dd_data=dd_data)


# wind distribution and energy production
@app.route('/Wind', methods=['GET', 'POST'])
def Wind():

    # print('**********WindEnergy******', session['location'], session['city'])
    ff = str(session['id'])
    # with open('static/'+ff+'.json') as wthj:
    with open(session['locationJs']) as wthj:
        wth = json.load(wthj)
    session['wchartstart_hr'] = 0
    session['wchartend_hr'] = 8670
    session["TURBD"] = 3 
    session["TURBH"] = 100
    if request.method == "GET":
        if session["TURBD"] == "": session["TURBD"] = 3
        if session["TURBH"] == "": session["TURBH"] = 100
        we = cc.windEnergy(wth["wv"], session["TURBD"], session["TURBH"])
        dataW = {'windv': wth['wv'],'winda':  wth['wd'], 'windp':we.P ,'windtc': we.WTPCurve00, 'windtcdefault':we.WTPCdefault}
        # print ('////////',dataW['windp'])
    
    if request.method == 'POST':
        if 'submitWindEnergy' in request.form:
            post_d = (request.form['turb_d'])
            post_h = (request.form['turb_h'])
            if post_d != None and post_d != "" : session["TURBD"] = round(float(post_d),1) 
            if post_h != None and post_h != "" : session["TURBH"] = round(float(post_h),1) 

        we = cc.windEnergy(wth["wv"], session["TURBD"], session["TURBH"])
        dataW = {'windv': wth['wv'],'winda':  wth['wd'], 'windp':we.P ,'windtc': we.WTPCurve00, 'windtcdefault':we.WTPCdefault}
        
        if 'submitWindRose' in request.form:
            wchartstart_hr = (request.form['start_hr'])
            wchartend_hr = (request.form['end_hr'])

            if wchartstart_hr != None and wchartstart_hr != "" : session['wchartstart_hr'] = wchartstart_hr
            if wchartend_hr != None and wchartend_hr != "" :session['wchartend_hr'] = wchartend_hr

            # print ('000000', session['wchartstart_hr'] , session['wchartend_hr']  )

    return render_template("Wind.html", dataW = dataW)


# @app.route('/cookie/')
# def cookie():
#     res = make_response("Setting a cookie")
#     res.set_cookie('checkboxValues', '{"nv":true,"h":false,"c":true}', max_age=None)
#     return res

# climabox indoor conditions
@app.route('/Climabox', methods=['GET', 'POST'])
def Climabox():
    ff = str(session['id'])
    with open(session['locationJs']) as wthj:
    # with open('static/'+ff+'.json') as wthj:
        wth = json.load(wthj)

    dd = wth['db']
    wind_d = wth['wd']
    wind_v = wth['wv']
    LPD, EPD = 10,10  
    # **************
    # if session.get('Hcop') == True: print ('*/*/*/*/ Heating is on')
    # else: session['Hcop']=0.85
    # if session.get('Ccop') == True: print ('*/*/*/*/ Cooling is on')
    # else: session['Ccop']=3
    # if session.get('NVach') == True: print ('*/*/*/*/ NV is available')
    # else: session['NVach']=0

    # system_ = (request.form.getlist('system'))
    # if len(system_) != 0: 
    #     if 'h' in system_: session['Hcop'] = 1
    #     else: session['Hcop'] = 0
    #     if 'c' in system_: session['Ccop'] = 1
    #     else: session['Ccop'] = 0
    #     if 'nv' in system_: session['NVach'] = 1
    #     else: session['NVach'] = 0
    # **************
    # 'V_dot':(0.6*10*10*3/3600)
    zone_input = {'L':10,'W':10,'H':3,'WWRs':0.3, 'WWRw':0.3, 'WWRn':0.3, 'WWRe':0.3,
                'U_wall':0.34,'U_roof':0.33,'U_glazing':3.4,
                'V_dot':(0.6*10*10*3/3600),
                'A_TM_factor':1, 'T_TM': 0.04, 'cp_TM':1000, 'density_TM':2200,
                'h_convection':5, 'shgc':0.59, 'shadingFac':0.7,
                'sp_lower':18, 'sp_upper':26,
                'Hcop':0.85, 'Ccop':3, 'NVach':0, 
                'coef_CO2elec':0.275, 'coef_CO2gas':0.18, 'coef_Costgas':0.04, 'coef_Costelec':0.20}

    # if request.form.get('nventilation') != None: zone_input['NVach'] = float(request.form.get('nventilation'))
    # if request.form.get('system')!= None: 
    #     system = request.form.get('system').split('|')
    #     zone_input['Hcop'] = float(system[0])
    #     zone_input['Ccop'] = float(system[1])

    lat, lon, tz = round((float(wth['latitude'])),0), round((float(wth["longitude"]))*-1,0), round((float(wth["timezone"]))*-15,0)
    rf = cc.radFacade(lat,lon,wth['radn'], wth['radd'],wth['radg'])

    # run_ = cb.runRC(dd,wind_d,wind_v,rf.radHS,rf.radHW,rf.radHN,rf.radHE,zone_input,LPD,EPD)
    run_ = cb.runRC(dd,wind_d,wind_v,rf.dirradHS,rf.dirradHW,rf.dirradHN,rf.dirradHE,zone_input,LPD,EPD) #,session['Hcop'],session['Ccop'], session['NVach'])
  
    EUI_H_ = run_[4]
    EUI_C_ = run_[5]
    EUI_L, EUI_E = run_[6], run_[7]
    EUI_ = EUI_C_+EUI_H_+EUI_L+EUI_E
    CO2_ELEC, CO2_GAS = run_[9], run_[10]
    COST_ELEC, COST_GAS = run_[11], run_[12]

    dataT = {'Heating':run_[0], 'Cooling':run_[1], 'NV':run_[8], 'Tout':dd, 'Tin':run_[3], 'Tin_freq':run_[13],
            'Qh_T':EUI_H_, 'Qc_T':EUI_C_,'Ql_T':EUI_L,'Qe_T':EUI_E, 'EUI':EUI_, 'DisCold':run_[2][0], 'DisHot':run_[2][1],
            'CO2_Elec':CO2_ELEC, 'CO2_Gas':CO2_GAS, 'Cost_Elec':COST_ELEC, 'Cost_Gas':COST_GAS}

    if request.method == 'POST':
        if request.form['climaWidth'] == "": zone_input['W'] = 10
        else: zone_input['W'] = float(request.form['climaWidth'])
        if request.form['climaLength'] == "": zone_input['L'] = 10
        else: zone_input['L'] = float(request.form['climaLength'])
        if request.form['climaHeight'] == "": zone_input['H'] = 3
        else: zone_input['H'] = float(request.form['climaHeight'])
        
        zone_input['WWRn'] = float(request.form.get('wwrN'))
        zone_input['WWRs'] = float(request.form.get('wwrS'))
        zone_input['WWRw'] = float(request.form.get('wwrW'))
        zone_input['WWRe'] = float(request.form.get('wwrE'))

        zone_input['A_TM_factor'] = float(request.form.get('tm'))
        zone_input['U_roof'] = float(request.form.get('Rroof'))
        zone_input['U_wall'] = float(request.form.get('Rwall'))
        u_shgc = request.form.get('Uglazing').split('|')
        zone_input['U_glazing'] = float(u_shgc[0]) 
        zone_input['shgc'] = float(u_shgc[1])  
        inf_ = float(request.form.get('infiltration'))*zone_input['W']*zone_input['L']*zone_input['H']/3600
        zone_input['V_dot'] = inf_

        LPD = float(request.form.get('LPD'))
        EPD = float(request.form.get('EPD'))

        zone_input['NVach'] = float(request.form.get('nventilation'))
        # system = (request.form.getlist('system'))
        # if 'h' in system: session['Hcop'] = 1  
        # if 'c' in system: session['Ccop'] = 1
        # system = request.form.get('system').split('|')
        # zone_input['Hcop'] = float(system[0])
        # zone_input['Ccop'] = float(system[1])
        zone_input['Hcop'] = float(request.form.get('systemH'))
        zone_input['Ccop'] = float(request.form.get('systemC'))
        zone_input["coef_CO2elec"] = float(request.form.get('CO2Elec'))
        zone_input["coef_CO2gas"] = float(request.form.get('CO2Gas'))
        zone_input["coef_Costgas"] = float(request.form.get('CostGas'))
        zone_input["coef_Costelec"] = float(request.form.get('CostElec'))

        run = cb.runRC(dd,wind_d,wind_v,rf.dirradHS,rf.dirradHW,rf.dirradHN,rf.dirradHE,zone_input,LPD,EPD) #,session['Hcop'],session['Ccop'],session['NVach'])
        EUI_H = run[4]
        EUI_C = run[5]
        EUI_L, EUI_E = run[6], run[7]
        EUI = EUI_H+EUI_C+EUI_L+EUI_E
        
        dataT['Heating'] = run[0]
        dataT['Cooling'] = run[1]
        dataT['NV'] = run[8]
        dataT['Tin'] = run[3]
        dataT['Tin_freq']=run[13]
        dataT['Qh_T'] = EUI_H
        dataT['Qc_T'] = EUI_C
        dataT['Ql_T']=EUI_L
        dataT['Qe_T']=EUI_E
        dataT['EUI'] = EUI
        dataT['DisCold'] = run[2][0]
        dataT['DisHot'] = run[2][1]
        dataT['CO2_Elec'], dataT['CO2_Gas'] = run[9], run[10]
        dataT['Cost_Elec'], dataT['Cost_Gas'] = run[11], run[12]

    return render_template("Climabox.html", dataT=dataT, climabox=zone_input)

import app_host

if __name__ == "__main__":

    app_host.runHost(app)
