# -*- coding: utf-8 -*-
"""
@author: Elliot Brandwein and Dana Bakalar
"""
import easygui as g
import pymice as pm
import glob
import pandas as pd
import datetime
import os
assignedcorner = 0

#helper functions
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
        print(phase.get("Phase"))
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
    if(ec[0].Illumination < 5):
        current_phase = 'Dark'
    else:
        current_phase = 'Light'
    
    #Find first phase    
    if(current_phase == 'Dark'):
        while(duration < Dark):
            printed = False
            if(ec[end_phase_index].Illumination >= 5):
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
            if(ec[end_phase_index].Illumination < 5):
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


def AssignedCorner(animal, PL):        
    visits_corners = PL.getVisits(mice = animal)
    for v in visits_corners:
        if v.Module == "PlaceLearning" and v.PlaceError == 0:
            assignedcorner= v.Corner
            return(assignedcorner)     


###########################################################################################
#find and open the data, assign it a name
ending = '\*.zip'
msg, title ="Please select the folder containing your Place and Reversal learning data files", "Import PL/RL Data"
data = g.diropenbox(msg, title)
data = data + ending

PL_data = sorted(glob.glob(data), key=os.path.getmtime)
loaders = [pm.Loader(filename, getEnv=True) for filename in PL_data]
PL = pm.Merger(*loaders, getEnv=True)

msg, title  ="Name your Data","Name Data"
name = g.enterbox(msg, title) 
excelname =name + ".xlsx"
writer = pd.ExcelWriter(excelname, engine='xlsxwriter')

#set up data frame
cols = ["Name","Sex","Group", "Phase", "Phase Cycle", "Avg NPs per Visit"]


df_Place = pd.DataFrame(columns = cols)


#Extract first phase of Place Learning for each half hour analysis
phases = get_phases(PL.getEnvironment())
phase_count = len(phases)
for group in PL.getGroup():
    for animal in list(PL.getGroup(group).Animals):
        for phase in range(phase_count):
            new_row = {'Name':animal.Name, 'Sex':animal.Sex,
                       'Group': group,'Phase':phase + 1}
            df_Place = df_Place.append(new_row,ignore_index=True)

###########################################################################################################

index = 0
for group in PL.getGroup():
    for animal in list(PL.getGroup(group).Animals):
        assignedcorner = str(AssignedCorner(animal, PL))
        for phase in phases:
            visits = PL.getVisits(start = phase['Start'], end = phase['End'], mice = animal)
            module, lick_total, visit_count_total, np_count_total  = "na", 0,0,0
            licktime = datetime.timedelta(0)
            visit_duration_total = datetime.timedelta(0)
            np_duration_total = datetime.timedelta(0)            

            for visit in visits:
                visit_duration_total += visit.Duration
                visit_count_total += 1
                lick_total += visit.LickNumber
                module = visit.Module
                for nosepoke in visit.Nosepokes:
                    np_count_total += 1
                    licktime += nosepoke.LickContactTime
                    np_count_total += 1
                    np_duration_total += nosepoke.Duration
                    
                    
            visit_avg = datetime.timedelta(0)
            np_avg = datetime.timedelta(0)
            if(visit_count_total > 0):
                visit_avg = visit_duration_total / visit_count_total
            if(np_count_total > 0):
                np_avg = np_duration_total / np_count_total
                
            #calculate place-learning specific stuff        
            correctpokes,incorrectpokes,prevCornerErrs, percent_prevCornerErrs, \
            npErrs, percentnp_Errs, errs, npPCErrs, percent_Errs,\
            percent_npPCErrs,  = 0,0,0,0,0,0,0,0,0,0 
            for v in visits:                        
                if v.PlaceError == 1:
                    incorrectpokes += 1
                    errs += 1
                    npErrs += v.NosepokeNumber
                if v.Module == "ReversalLearning":                      
                    if assignedcorner == "1" and str(v.Corner) == "1":
                        prevCornerErrs += 1
                    if assignedcorner == "2" and str(v.Corner) == "2":
                        prevCornerErrs += 1
                    if assignedcorner == "3" and str(v.Corner) == "3":
                        prevCornerErrs += 1
                    if assignedcorner == "4" and str(v.Corner) == "4":
                        prevCornerErrs += 1                    
                if visit_count_total > 1:
                    percent_Errs = errs/len(visits)
                    percent_prevCornerErrs = prevCornerErrs/len(visits) 
                else:
                    percent_prevCornerErrs = 0
                    percent_Errs = 0
      
                if np_count_total > 1:
                    percentnp_Errs = npErrs/np_count_total  
                else: percentnp_Errs = 0
            
            df_Place.at[index,"Phase Length (M)"] = phase['Duration']
            df_Place.at[index,"Phase Cycle"] = phase['Phase']
            df_Place.at[index, "Module"]  = module  
            
            df_Place.at[index,"Total Visits"] = visit_count_total
            df_Place.at[index,"Avg Duration of Visits (s)"] = visit_avg.microseconds / 1000000
            df_Place.at[index,"Total Nosepokes"] = np_count_total
            df_Place.at[index,"Avg Duration of NP (s)"] = np_avg.microseconds / 1000000
            if(visit_count_total > 0):
                df_Place.at[index,"Avg NPs per Visit"] = \
                np_count_total / visit_count_total

            df_Place.at[index,"Total Licks"] = lick_total
            df_Place.at[index,"Lick Time"] = licktime.microseconds / 100000   
            df_Place.at[index, "Incorrect_Vis_Percent"] = percent_Errs
            df_Place.at[index, "Incorrect_NP_Percent"] = percentnp_Errs
            df_Place.at[index, "Prev_corner_errs"]= percent_prevCornerErrs
            index += 1
 
df_Place.to_excel(writer, sheet_name = 'Place and reversal learning')

writer.save()

