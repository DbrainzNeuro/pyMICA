

# -*- coding: utf-8 -*-
"""
Created on Thu Oct 11 09:46:02 2018

@author: Dana Bakalar and Elliot Brandwein
"""

import pymice as pm
import easygui as g
import pandas as pd
import datetime
import glob
import os
###################################################################################

#Functions needed
def cleanUp(listofvisits):
     deleteindexes =[]
     removedvisits = []
     for v in listofvisits:
         seconds = v.Duration.total_seconds()
         pokes = v.NosepokeNumber
#locate visits with no pokes or lasting more than 2 minutes         
#remove these visits from the visits to be analyzed
         if seconds > 180 or pokes == 0:
             j = listofvisits.index(v)
             deleteindexes.append(j)
     for k in reversed(deleteindexes):
         removedvisits.append(listofvisits[k])
         del(listofvisits[k])
     return(listofvisits, removedvisits)
     

def Early_Late(v):
#called for each visit within a mouse/phase combo
    visit_module, c = 0, 0
    if v.Module == 'Delay0.5':
        visit_module = 0.5 
    elif v.Module == 'Delay1.5':
        visit_module = 1.5     
    elif v.Module == 'Delay2.5':
        visit_module = 2.5  
    late = visit_module + 5
    early = visit_module 
    nps = []
    EarlyPokes, LatePokes, OnTimes, omissions, rt = 0,0,0, 0, 0
   
    if v.Module != "Default":
        for n in range(len(v.Nosepokes)): 
            m = v.Nosepokes[n] #get each nosepoke in range
            nps.append(m.Start)  #list the times each np starts
    
            a = nps[n] #start of THIS nosepoke
            b= nps[0] #start of first nosepoke
            c=a-b #time difference between the two pokes
            if c.total_seconds() < early and c.total_seconds() > 0:
                EarlyPokes = EarlyPokes + 1
            elif c.total_seconds() > late:
                LatePokes=LatePokes+1
            elif c.total_seconds() >= early and c.total_seconds() < late:
                OnTimes = OnTimes + 1
            
            if c.total_seconds() >= early and rt == 0:
                rt = c.total_seconds()
                
        if len(nps)> 1:
            d = nps[1] #start of second nosepoke- for measuring omissions
            e = d-b
            if e.total_seconds() > late:
                omissions += 1       
            
    return (EarlyPokes, LatePokes, OnTimes, rt, omissions)

   
   
   for n in range(len(v.Nosepokes)):
       n0 = v.Nosepokes[0]
       toolate = n0.Start + datetime.timedelta(0,late)
       m = v.Nosepokes[n]
       if m.SideCondition == 1 and m.Start > toolate:
          SideErrors += 1
   return(SideErrors)


def CorrectList(v):
    list_withcorrect=[]
    corrects = 0
    for n in range(len(v.Nosepokes)): 
        m = v.Nosepokes[0]
        correct = m.Side
        o0 = v.Nosepokes[n]
        o = o0.Side
        if o == correct:
            list_withcorrect.append(o)
        if len(list_withcorrect) >= 1:
            corrects = 1   #there was at least one correct poke after the initial one this visit
    return corrects

def calc_end_phase_index(phase_len,begin_index,ec):
    end_index = begin_index + 1
    while(get_timedelta_in_minutes(ec[begin_index].DateTime,ec[end_index].DateTime) < phase_len):
        end_index += 1    
    return end_index
    
def get_timedelta_in_minutes(start,end):
    timedelta = (end - start)
    timedelta = (timedelta.total_seconds()/60)
    return round(timedelta)

def print_time_data(phases):
    for phase in phases:
        print("start time: " + str(phase.get('Start')), "end time: " +
          str(phase.get('End')), "delta: " + str((phase.get('End') -
          phase.get('Start')) / datetime.timedelta(minutes=1)))

def get_phases(EnvironmentalConditions,*,Light=720,Dark=720):
    begin_phase_index = 0
    end_phase_index = 0
    output = []
    ec = EnvironmentalConditions
    run_time = (get_timedelta_in_minutes(ec[0].DateTime,ec[len(ec)-1].DateTime))
    current_phase = ""
    duration = 0
    if(ec[0].Illumination < 4):
        current_phase = 'Dark'
    else:
        current_phase = 'Light'
    
    #Find first phase    
    if(current_phase == 'Dark'):
        while(duration < Dark):
            printed = False
            if(ec[end_phase_index].Illumination >= 4):
                output.append({ 
                    'Start':ec[begin_phase_index].DateTime,
                    'End':ec[end_phase_index].DateTime,
                    'Duration':duration,'Phase':current_phase})
                begin_phase_index = end_phase_index + 1
                current_phase = 'Light'
                printed = True
                break
            else:
                end_phase_index += 1
                duration = get_timedelta_in_minutes(ec[0].DateTime,
                  ec[end_phase_index].DateTime)
        if(not printed):
          output.append({ 
            'Start':ec[begin_phase_index].DateTime,
            'End':ec[end_phase_index].DateTime,
            'Duration':duration,'Phase':current_phase})
          begin_phase_index = (end_phase_index + 2)
          current_phase = 'Light'
               
    elif(current_phase == 'Light'):
        while(duration < Light):
            printed = False
            if(ec[end_phase_index].Illumination < 4):
                output.append({ 
                'Start':ec[begin_phase_index].DateTime,
                'End':ec[end_phase_index].DateTime,
                'Duration':duration,'Phase':current_phase})
                begin_phase_index = (end_phase_index + 1)
                current_phase = 'Dark'
                printed = True
                break
            else:
                end_phase_index += 2
                duration = get_timedelta_in_minutes(ec[0].DateTime,
                                      ec[end_phase_index].DateTime)
        if(not printed):
          output.append({ 
            'Start':ec[begin_phase_index].DateTime,
            'End':ec[end_phase_index].DateTime,
            'Duration':duration,'Phase':current_phase})
          begin_phase_index = (end_phase_index + 1)
          current_phase = 'Dark'      

    #get the middle phases
    run_time -= duration
    while(((current_phase == 'Dark') and run_time - Dark > 0) or 
        ((current_phase == 'Light') and run_time - Light > 0)):
        if(current_phase == 'Dark'):
            end_phase_index = calc_end_phase_index(Dark,begin_phase_index,ec)
            run_time -= Dark
            output.append({'Start':ec[begin_phase_index].DateTime,
              'End':ec[end_phase_index].DateTime,
              'Duration':Light,'Phase':current_phase})
            current_phase = 'Light'
            begin_phase_index = (end_phase_index + 1)
        else:
            end_phase_index = calc_end_phase_index(Light,begin_phase_index,ec)
            run_time -= Light
            output.append({'Start':ec[begin_phase_index].DateTime,
              'End':ec[end_phase_index].DateTime,
              'Duration':Light,'Phase':current_phase})
            current_phase = 'Dark'
            begin_phase_index = (end_phase_index + 1)
    #get last phase
    output.append({
         'Start':ec[begin_phase_index].DateTime,
         'End':ec[len(ec) -1].DateTime,
         'Duration':Light,'Phase':current_phase
        })
    print_time_data(output)
    return output   
     
################################################################################
#find and open the data, assign it a name
ending = '\*.zip'
msg, title ="Please select the folder containing your SRT data files", "Import SRT Data"
data = g.diropenbox(msg, title)
data = data + ending

SRT_data = sorted(glob.glob(data), key=os.path.getmtime)
loaders = [pm.Loader(filename, getEnv=True) for filename in SRT_data]
SRT = pm.Merger(*loaders, getEnv=True)

msg, title  ="Name your Data","Name Data"
name = g.enterbox(msg, title) 
excelname =name + ".xlsx"



#set up data frame
columns05 = ["Name","Sex","Group","Phase", "Phase Length (M)","Phase Cycle",
          
           "Visits","Nosepokes", 
           "Side Errors","Early Pokes",
           "Late Pokes", "Reaction Time (s)", "Omissions"]
           
columns15 = ["Name","Sex","Group","Phase", "Phase Length (M)","Phase Cycle",
          
           "Visits","Nosepokes", 
           "Side Errors","Early Pokes",
           "Late Pokes", "Reaction Time (s)", "Omissions"]

columns25 = ["Name","Sex","Group","Phase", "Phase Length (M)","Phase Cycle",
          
           "Visits","Nosepokes", 
           "Side Errors","Early Pokes",
           "Late Pokes", "Reaction Time (s)", "Omissions"]

data_frame05 = pd.DataFrame(columns = columns05)
data_frame15 = pd.DataFrame(columns = columns15)
data_frame25 = pd.DataFrame(columns = columns25)

phases = get_phases(SRT.getEnvironment())
phase_count = len(phases)
for group in SRT.getGroup():
    for animal in list(SRT.getGroup(group).Animals):
        for phase in range(phase_count):
            new_row = {'Name':animal.Name, 'Sex':animal.Sex,
                       'Group': group,'Phase':phase + 1}
            data_frame05 = data_frame05.append(new_row,ignore_index=True)
            data_frame15 = data_frame15.append(new_row,ignore_index=True)
            data_frame25 = data_frame25.append(new_row,ignore_index=True)
            
            

 
index = 0
for group in SRT.getGroup():
    for animal in list(SRT.getGroup(group).Animals):
        for phase in phases:
            omissions05, omissions15, omissions25 = 0,0,0
#collect the visits
            visits_uncleaned = SRT.getVisits(start = phase['Start'], end = phase['End'], mice = animal)
            visits, removedvisits = cleanUp(visits_uncleaned)

#Reset all variables for this mouse and phase                  
            withcorrect05,withcorrect15,withcorrect25= 0,0,0
            visits05,visits15,visits25= 0,0,0
            all_early05,all_early15,all_early25 = 0,0,0
            all_lates05,all_lates15,all_lates25 =0,0,0
            ontimes05,ontimes15,ontimes25 =0,0,0
            pokes05,pokes15,pokes25 = 0,0,0           
            reacttimes05,reacttimes15,reacttimes25 =[],[],[]

            
#get statistics for each visit   
            for v in visits:
                FinalErrs = SideErrors(v) 
                correct = CorrectList(v)   
                EarlyPokes, LatePokes, OnTimes, rt, omissions = Early_Late(v)  
        #sort these statistics based on module  : for v in visits:           
                if v.Module == 'Delay0.5':
                    visits05  +=  1 #count visits at each delay
                    pokes05 += v.NosepokeNumber #count nosepokes this visit 
                    side_r05 += FinalErrs
                    withcorrect05  +=  correct
                    all_early05 += EarlyPokes
                    all_lates05 += LatePokes          
                    reacttimes05.append(rt)  #this is the reaction time in seconds   
                    omissions05 += omissions 
                    if OnTimes != 0:
                        ontimes05 += OnTimes
                        
                elif v.Module == 'Delay1.5':
                    visits15  +=  1
                    pokes15 += v.NosepokeNumber
                    side_r15 += FinalErrs
                    withcorrect15  += correct
                    all_early15 += EarlyPokes
                    all_lates15 += LatePokes
                    reacttimes15.append(rt)  #this is the reaction time  
                    omissions15 += omissions
                    if OnTimes != 0:
                        ontimes15 += OnTimes
                                                    
                elif v.Module == 'Delay2.5':
                    visits25 = visits25 + 1
                    pokes25 += v.NosepokeNumber
                    side_r25 += FinalErrs
                    withcorrect25 = withcorrect25 + correct
                    all_early25 += EarlyPokes
                    all_lates25 += LatePokes
                    reacttimes25.append(rt)  #this is the reaction time   
                    omissions25 += omissions
                    if OnTimes != 0:
                        ontimes25 += OnTimes

            data_frame05.at[index,"Phase Length (M)"] = phase['Duration']
            data_frame05.at[index,"Phase Cycle"] = phase['Phase']
            data_frame15.at[index,"Phase Length (M)"] = phase['Duration']
            data_frame15.at[index,"Phase Cycle"] = phase['Phase']
            data_frame25.at[index,"Phase Length (M)"] = phase['Duration']
            data_frame25.at[index,"Phase Cycle"] = phase['Phase']
               
            data_frame05.at[index,"Visits"] = visits05
            data_frame15.at[index,"Visits"] = visits15
            data_frame25.at[index,"Visits"] = visits25
        
            data_frame05.at[index,"Nosepokes"] = pokes05
            data_frame15.at[index,"Nosepokes"] = pokes15
            data_frame25.at[index,"Nosepokes"] = pokes25

            data_frame05.at[index,"Early Pokes"] = all_early05
            data_frame15.at[index,"Early Pokes"] = all_early15
            data_frame25.at[index,"Early Pokes"] = all_early25
        
            data_frame05.at[index,"Late Pokes"] = all_lates05
            data_frame15.at[index,"Late Pokes"] = all_lates15
            data_frame25.at[index,"Late Pokes"] = all_lates25
            
            data_frame05.at[index,"Omissions"] = omissions05
            data_frame15.at[index,"Omissions"] = omissions15
            data_frame25.at[index,"Omissions"] = omissions25
        
            if len(reacttimes05) > 0:
                data_frame05.at[index,"Reaction Time (s)"] = sum(reacttimes05)/len(reacttimes05)
            if len(reacttimes15) > 0:
                data_frame15.at[index,"Reaction Time (s)"] = sum(reacttimes15)/len(reacttimes15)
            if len(reacttimes25) > 0:
                data_frame25.at[index,"Reaction Time (s)"] = sum(reacttimes25)/len(reacttimes25)
            index += 1
            
writer = pd.ExcelWriter (excelname, engine = 'xlsxwriter')          
data_frame05.to_excel(writer, sheet_name='0.5 sec delay')
data_frame15.to_excel(writer, sheet_name='1.5 sec delay')
data_frame25.to_excel(writer, sheet_name='2.5 sec delay')

# Close the Pandas Excel writer and output the Excel file.
writer.save()
