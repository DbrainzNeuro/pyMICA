# -*- coding: utf-8 -*-
"""
Created on Fri Aug 16 09:43:19 2019

@author: Elliot Brandwein and Dana Bakalar
"""

import pymice as pm
import pandas as pd
import glob
import easygui as g
import datetime


#functions needed
def get_phases(EnvironmentalConditions,*,Light=720,Dark=720):
    output = []
    run_time = len(EnvironmentalConditions)
    current_phase = ""
    if(EnvironmentalConditions[0].Illumination < 30):
        current_phase = 'Dark'
    else:
        current_phase = 'Light'
    end_last_phase_index = 0
    
    #find first phase
    if(current_phase == 'Dark'):
        for x in range(1,Dark):
            if(EnvironmentalConditions[x].Illumination >= 30):
                output.append({'Start':EnvironmentalConditions[0].DateTime,
                               'End':EnvironmentalConditions[x].DateTime,
                               'Duration':x,'Phase':current_phase})
                end_last_phase_index = x
                current_phase = 'Light'
                break
    else:
      for x in range(1,Light):
          if(EnvironmentalConditions[x].Illumination < 30):
            output.append({'Start':EnvironmentalConditions[0].DateTime,
           'End':EnvironmentalConditions[x].DateTime, 
           'Duration':x,'Phase':current_phase})
            end_last_phase_index = x
            current_phase = 'Dark'
            break
        
    #find all middle phases
    while((run_time - end_last_phase_index > Dark and current_phase == 'Dark')
     or(run_time - end_last_phase_index > Light and current_phase == 'Light')):
            if(current_phase == 'Dark'):
                output.append(
         {'Start':EnvironmentalConditions[end_last_phase_index + 1].DateTime,
          'End':EnvironmentalConditions[end_last_phase_index + Dark].DateTime,
          'Duration':Dark,
          'Phase':current_phase})
                current_phase = 'Light'
                end_last_phase_index += Dark
            else:
                output.append(
        {'Start':EnvironmentalConditions[end_last_phase_index + 1 ].DateTime,
         'End':EnvironmentalConditions[end_last_phase_index + Light].DateTime,
         'Duration':Light,
         'Phase':current_phase})
                current_phase = 'Dark'
                end_last_phase_index += Light
                
    #calculate last phase
    if(current_phase == 'Dark'):
        output.append(
        {'Start':EnvironmentalConditions[end_last_phase_index + 1].DateTime,
         'End':EnvironmentalConditions[run_time - 1].DateTime,
         'Duration':run_time - end_last_phase_index + 1 ,
         'Phase':current_phase})
    else:
         output.append(
        {'Start':EnvironmentalConditions[end_last_phase_index + 1].DateTime,
         'End':EnvironmentalConditions[run_time - 1].DateTime,
         'Duration':run_time - end_last_phase_index + 1 ,
         'Phase':current_phase})
    return output    


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
     
     
############################################################################################
#find and open the data, assign it a name
#find and open the data, assign it a name
ending = '\*.zip'
msg, title ="Please select the folder containing your Habituation data files", "Import Habituation Data"
data = g.diropenbox(msg, title)
data = data + ending

DD_data = glob.glob(data)
loaders = [pm.Loader(filename, getEnv=True) for filename in DD_data]
DD = pm.Merger(*loaders, getEnv=True)

msg, title  ="Name your Data","Name Data"
name = g.enterbox(msg, title) 
excelname =name + ".xlsx"
writer = pd.ExcelWriter(excelname, engine='xlsxwriter')

                   
columns = ["Name","Sex","Group","Phase", "Phase Length (M)","Phase Cycle", "Delay",
           
           "Total Nosepokes", "NPs to Saccharine","Total Visits","Avg Duration of Visits (s)", 
           "Avg NPs per Visit","Total Licking Contact Time (s)", "Saccharine Licking Contact Time (s)", 
           "Saccharine Preference", "Premature Pokes to Saccharine", "Premature Pokes to Water"]

data_frame = pd.DataFrame(columns = columns)


phases = get_phases(DD.getEnvironment())
phase_count = len(phases)
for group in DD.getGroup():
    for animal in list(DD.getGroup(group).Animals):
        for phase in range(phase_count):
            new_row = {'Name':animal.Name, 'Sex':animal.Sex,
                       'Group': group,'Phase':phase + 1}
            data_frame = data_frame.append(new_row,ignore_index=True)
            
            
index = 0
delay = 0
for group in DD.getGroup():
    for animal in list(DD.getGroup(group).Animals):
        for phase in phases:     
            earlyPokes_sac, earlyPokes_water = 0,0
            licks_sac, lick_total, nps_sac,nps_water = 0,0,0,0
            visit_count_total,np_count_total = 0,0
            visit_duration_total = datetime.timedelta(0)
            
#get Visits
            visitsuncleaned = DD.getVisits(start = phase['Start'],
                                         end = phase['End'],
                                         mice = animal)
#Clean data,  removing visits with 0 pokes and visits longer than 180 seconds
            visits, removed = cleanUp(visitsuncleaned)

            for visit in visits:
                module = visit.Module
                if module == "Default":
                    delay = 0
                if module == "0.5s delay":
                    delay = 0.5
                if module == "1s delay":
                    delay = 1
                if module == "1.5s delay":
                    delay = 1.5
                if module == "2s delay":
                    delay = 2
                if module == "2.5s delay":
                    delay = 2.5
                if module == "3s delay":
                    delay = 3
                if module == "3.5s delay":
                    delay = 3.5
                if module == "4s delay":
                    delay = 4
                if module == "4.5s delay":
                    delay = 4.5
                if module == "5s delay":
                    delay = 5
                if module == "5.5s delay":
                    delay = 5.5
                if module == "6s delay":
                    delay = 6
                if module == "6.5s delay":
                    delay = 6.5 
                if module == "7s delay":
                    delay = 7
                if module == "7.5s delay":
                    delay = 7.5 
                if module == "8s delay":
                    delay = 8


#find number of early pokes to saccharine 
                nps = []
                for n in range(len(visit.Nosepokes)): 
                    m = visit.Nosepokes[n] #get each nosepoke in range
                    nps.append(m.Start)  #list the times each np starts
                    a = nps[n] #start of THIS nosepoke
                    b= nps[0] #start of first nosepoke
                    c=a-b
                    if c.seconds < delay:
                        if m.SideError == 0:
                            earlyPokes_sac += 1
                        if m.SideError == 1:
                            earlyPokes_water += 1

                
                a = visit.Nosepokes
                np_count_total += len(a)
                for n in a:
                    lick_total += n.LickContactTime.microseconds
                    if n.SideError == 0:   #this means a poke to the saccharine        
                        nps_sac += 1
                        licks_sac += n.LickContactTime.microseconds
                visit_count_total += 1
                visit_duration_total += visit.Duration
            visit_avg = datetime.timedelta(0)
            np_avg = datetime.timedelta(0)
            if(visit_count_total > 0):
                visit_avg = visit_duration_total / visit_count_total
            if(lick_total > 0):
                data_frame.at[index,"Saccharine Preference"] = (licks_sac/lick_total)
            data_frame.at[index,"Phase Length (M)"] = phase['Duration']
            data_frame.at[index,"Delay"] = delay
            data_frame.at[index,"Premature Pokes to Saccharine"] = earlyPokes_sac
            data_frame.at[index,"Premature Pokes to Water"] = earlyPokes_water
            data_frame.at[index,"Saccharine Licking Contact Time (s)"] =licks_sac/1000
            data_frame.at[index,"Phase Cycle"] = phase['Phase']
            data_frame.at[index,"Total Visits"] = visit_count_total
            data_frame.at[index,"Total Nosepokes"] = np_count_total
            data_frame.at[index,"NPs to Saccharine"] = nps_sac
            data_frame.at[index,"Total Licking Contact Time (s)"] = lick_total/1000
            data_frame.at[index,"Avg Duration of Visits (s)"] = visit_avg.microseconds / 1000000
            if visit_count_total > 0:
                data_frame.at[index,"Avg NPs per Visit"] = np_count_total/visit_count_total
            index += 1
           

#save the data as an excel file
data_frame.to_excel(writer, sheet_name='By Phase') 

writer.save()






