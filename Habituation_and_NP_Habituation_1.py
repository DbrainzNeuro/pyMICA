# -*- coding: utf-8 -*-
"""
Created on Tue Jul 30 09:54:42 2019
@author: Elliot Brandwein and Dana Bakalar
"""    

import pymice as pm
import pandas as pd
import glob
import datetime
import easygui as g

#helper functions 
def cleanUp(listofvisits,*,seconds=180,pokes=0):
     deleteindexes =[]
     removedvisits = []
     for v in listofvisits:
         seconds = v.Duration.total_seconds()
         pokes = v.NosepokeNumber
#locate visits with no pokes or lasting more than 2 minuhgtes         
#remove these visits from the visits to be analyzed
         if seconds > 180 or pokes == 0:
             j = listofvisits.index(v)
             deleteindexes.append(j)
     for k in reversed(deleteindexes):
         removedvisits.append(listofvisits[k])
         del(listofvisits[k])
     return(listofvisits)

def Alternation(explorevisits):
     from numpy import unique
#get spontaneous alternation for 1st 100 visits 
     altVisits = explorevisits[:100]
     startscan = 0
     startscan2 = 3
     allEntries =[]
     SCA=0
     ACR=0
     SCR =0     
     for v in altVisits:
         a = v.Corner
         allEntries.append(a)
         tri =  allEntries[startscan:startscan2]
         if len(tri)==3:
             if len(unique(tri)) == 3:
                   SCA = SCA + 1
                   startscan = startscan + 1
                   startscan2 = startscan2 + 1
             elif tri[0] != tri[1] and tri[0] == tri[2]:
                   ACR = ACR + 1
                   startscan = startscan + 1
                   startscan2 = startscan2 + 1
             elif tri[0] == tri[1] or tri[1] == tri[2]:
                   SCR = SCR + 1
                   startscan = startscan + 1
                   startscan2 = startscan2 + 1 
     SCA = (SCA/98)*100
     ACR = (ACR/98)*100
     SCR = (SCR/98)*100
     return(SCA,ACR,SCR)     
     

#calculates the latency to visit all 4 corners of the cage for each mouse: 
# a measure of exploration akin to open field
def ExplorePhase(explorevisits):
    latency = 0
    if len(explorevisits)> 1:
        e = explorevisits[0]
        time0 =  e.Start
        side0 = e.Corner
        cornersvisited = [side0]
        for f in explorevisits:
             if f.Corner not in cornersvisited:
                  cornersvisited.append(f.Corner)
                  lat = f.Start-time0
                  latency = lat.seconds
    return(latency)

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
    if(ec[0].Illumination < 15):
        current_phase = 'Dark'
    else:
        current_phase = 'Light'
    
    #Find first phase    
    if(current_phase == 'Dark'):
        while(duration < Dark):
            printed = False
            if(ec[end_phase_index].Illumination >= 15):
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
            if(ec[end_phase_index].Illumination < 15):
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



##################################################################################
#find and open the data, assign it a name
ending = '\*.zip'
msg, title ="Please select the folder containing your Habituation data files", "Import Habituation Data"
data = g.diropenbox(msg, title)
data = data + ending
Habit_data = glob.glob(data)
loaders = [pm.Loader(filename, getEnv=True) for filename in Habit_data]
habit = pm.Merger(*loaders, getEnv=True)


msg, title  ="Name your Data","Name Data"
name = g.enterbox(msg, title) 
excelname =name + ".xlsx"
writer = pd.ExcelWriter(excelname, engine='xlsxwriter')


hr1visits, hr48visits= 0, 0           
index2 = 0
phases = get_phases(habit.getEnvironment())
phase_count = len(phases)


columns = ["Name","Sex","Group"]
columns2 = ["Name","Sex","Group","Latency_to_four","Spontaneous_Corner_Alternations",
            "Alternate_Corner_Returns","Same_Corner_Returns", "Circadian_Ratio", 
            "Visits_First_Hour", "Visits_48th_Hour"]
data_frame = pd.DataFrame(columns = columns)
data_frame2 = pd.DataFrame(columns = columns2)


#fill in headers of data frame 1
for group in habit.getGroup():
    for animal in list(habit.getGroup(group).Animals):
        for phase in range(phase_count):
            new_row = {'Name':animal.Name, 'Sex':animal.Sex,
                       'Group': group,'Phase':phase + 1}
            data_frame = data_frame.append(new_row,ignore_index=True)

#fill in headers of data frame 2
for group in habit.getGroup():
    for animal in list(habit.getGroup(group).Animals):
        new_row = {'Name':animal.Name, 'Sex':animal.Sex,
                       'Group': group}
        data_frame2 = data_frame2.append(new_row,ignore_index=True)
        
#get Spontaneous Corner Alternation info and Latency to explore 4 corners from uncleaned data 
        explorevisits = habit.getVisits(mice= animal)
        print(len(explorevisits))
        SCA,ACR,SCR = Alternation(explorevisits)
        latency = ExplorePhase(explorevisits)
        
        data_frame2.at[index2,"Latency_to_four"] = latency
        data_frame2.at[index2,"Spontaneous_Corner_Alternations"] = SCA
        data_frame2.at[index2,"Alternate_Corner_Returns"] = ACR
        data_frame2.at[index2,"Same_Corner_Returns"] = SCR
    
#get circadian ratio of the mice
#NOTE: higher values on this measure of DayPattern indicate reduced activity during the day         
        lightvisits = 0
        darkvisits = 0
        for phase in phases:
            visits = habit.getVisits(start = phase.get("Start"),
                        end = phase.get("End"),mice = animal)
            Light_or_Dark = phase.get("Phase")
            if Light_or_Dark == "Dark":
                darkvisits += len(visits)
            if Light_or_Dark == "Light":
                lightvisits += len(visits)
        if lightvisits + darkvisits > 1:
            circ = (darkvisits-lightvisits)/(lightvisits+darkvisits)
            data_frame2.at[index2,"Circadian_Ratio"] = circ
                
#check number of visits in first hour in the cage and the equivalent timepoint 48 hours later
        if len(explorevisits)>3:
            start_time = explorevisits[1].Start    
            firsthr = start_time + datetime.timedelta(hours = 1)
            fortyeight = start_time + datetime.timedelta(hours = 48)
            endfortyeight = start_time + datetime.timedelta(hours = 49)
            
            hr1visits = len(habit.getVisits(start = start_time,
                                         end = firsthr,
                                         mice = animal))
            hr48visits = len(habit.getVisits(start = fortyeight,
                                         end = endfortyeight,
                                         mice = animal))           
            data_frame2.at[index2,"Visits_First_Hour"] = hr1visits
            data_frame2.at[index2,"Visits_48th_Hour"] = hr48visits

        index2 += 1

#########################################################################################
# Prepare to collect data from each phase, resetting variables
index = 0
for animal in list(habit.getAnimal()):
    for phase in phases:
        lick_total = 0
        visit_count_total = 0
        np_count_total = 0
        visit_duration_total = datetime.timedelta(0)
        np_duration_total = datetime.timedelta(0)
        for visit in habit.getVisits(start = phase['Start'],
                                     end = phase['End'],
                                     mice = animal):
            visit_count_total += 1
            visit_duration_total += visit.Duration
            lick_total += visit.LickNumber
            for nosepoke in visit.Nosepokes:
                np_count_total += 1
                np_duration_total += nosepoke.Duration
        visit_avg = datetime.timedelta(0)
        np_avg = datetime.timedelta(0)
        if(visit_count_total > 0):
            visit_avg = visit_duration_total / visit_count_total
        if(np_count_total > 0):
            np_avg = np_duration_total / np_count_total
        data_frame.at[index,"Phase Length (M)"] = phase['Duration']
        data_frame.at[index,"Phase Cycle"] = phase['Phase']
        data_frame.at[index,"Total Visits"] = visit_count_total
        data_frame.at[index,"Total Nosepokes"] = np_count_total
        data_frame.at[index,"Total Licks"] = lick_total
        data_frame.at[index,"Avg Duration of NP (s)"] = np_avg.microseconds / 1000000
        data_frame.at[index,"Avg Duration of Visits (s)"] = visit_avg.microseconds / 1000000
        if(visit_count_total > 0):
            data_frame.at[index,"Avg NPs per Visit"] = \
                np_count_total / visit_count_total
        index += 1

# run to print data frame to spreadsheet

data_frame.to_excel(writer, sheet_name='All Phases')
data_frame2.to_excel(writer, sheet_name = 'Overall Statistics')


writer.save()

