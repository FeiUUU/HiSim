import globals
import numpy as np
import pandas as pd
import math
import json
import os
import pickle
import seaborn as sns
from string import digits
import re
#plot stuff
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import MaxNLocator
from matplotlib.pyplot import figure
import numpy_financial as npf
import postprocessing.postprocessing as pp

class  ElectricityPricesConfig:
    def __init__(self):
        self.electricity_price_from_grid_household=0.3205 #Euro/kwh
        self.annual_electricity_price_raising=0.015 #1.5%

    def calculate_electricity_price_from_grid_household(self, observation_period:int):
        counter=0
        list_electricity_price_from_grid_household=[]
        while counter<=observation_period:
            if counter==0:
                electricity_price_from_grid_household_new=self.electricity_price_from_grid_household
            else:
                electricity_price_from_grid_household_new=electricity_price_from_grid_household_new+electricity_price_from_grid_household_new*self.annual_electricity_price_raising
            list_electricity_price_from_grid_household.append(electricity_price_from_grid_household_new)
            counter=counter+1
        return list_electricity_price_from_grid_household


    def calculate_electricity_price_from_grid_industry(self, utilisation_hours, price_for_atypical_usage, provider_price , observation_period):
        # splitted in low_price, average and high, all fpr Mittelspannungsnetz
        #low Westfalen Weser Netz GmbH
        #average e-netz Südhessen AG
        #high bnNETZE GmbH Baden Würtenberg

        if utilisation_hours>=2500:
            if provider_price== "average":
                leistungspreis= 44.4 #Eurp/kW
                arbeitspreis= 0.0154 #Eurp/kWh
            elif provider_price== "high":
                leistungspreis= 169.9 #Eurp/kW
                arbeitspreis= 0.083 #Eurp/kWh
            elif provider_price == "low":
                leistungspreis= 73.6 #Eurp/kW
                arbeitspreis= 0.021 #Eurp/kWh

        elif utilisation_hours<2500:
            if provider_price== "average":
                leistungspreis=17.93
                arbeitspreis=0.026
            elif provider_price== "high":
                leistungspreis= 24.2 #Eurp/kW
                arbeitspreis= 0.0663#Eurp/kWh
            elif provider_price == "low":
                leistungspreis= 9.26 #Eurp/kW
                arbeitspreis= 0.0467#Eurp/kWh

        elif price_for_atypical_usage==True:
            if provider_price == "average":
                leistungspreis= 7.4 #Eurp/kW
                arbeitspreis= 0.0154
            elif provider_price== "high":
                leistungspreis= 28.19#Eurp/kW
                arbeitspreis= 0.083
            elif provider_price == "low":
                leistungspreis= 12.28#Eurp/kW
                arbeitspreis= 0.021
        list_leistungspreis_from_grid_industry = []
        list_arbeitspreis_from_grid_industry = []
        counter = 0
        while counter<=observation_period:
            list_leistungspreis_from_grid_industry.append(leistungspreis)
            list_arbeitspreis_from_grid_industry.append(arbeitspreis)
            counter=counter+1
        return list_leistungspreis_from_grid_industry, list_arbeitspreis_from_grid_industry


    def electricity_price_relative_to_pv_size(self, pv_size):
        if pv_size < 10:
            electricity_prize_into_grid = 0.0683
        elif pv_size < 40 and pv_size > 10:
            electricity_prize_into_grid = 0.0663
        elif pv_size > 40 and pv_size < 100 :
            electricity_prize_into_grid = 0.0519
        elif pv_size > 100:
            electricity_prize_into_grid = 0.0467
        return electricity_prize_into_grid


class BatteryDataConfig:
    lifetime=15 #years

class PostProcessor:
    def __init__(self,
                 folder_name : str, #folder has to be in results
                 json_file_name : str,
                 pickle_file_name:str,
                 start_date : str, #in
                 end_date : str,
                 heat_map_precision_factor: int,
                 observation_period=15,
                 plot_heat_map=True,
                 plot_all_houses=False,
                 plot_sfh=True,
                 plot_mfh=False,
                 plot_strategy_all=False,
                 plot_strategy_own_consumption=True,
                 plot_strategy_seasonal_storage=False,
                 plot_strategy_peak_shave_into_grid =False,
                 plot_own_consumption=False,
                 plot_autarky=False,
                 plot_net_present_value=True,
                 plot_LCOE=True,
                 plot_payback_periode=True,
                 plot_battery_and_pv=True,
                 plot_h2_storage_relative_demand=False,
                 plot_h2_storage_relative_battery=False,
                 plot_peak_shaving_demand_accurancy=False,
                 plot_peak_shaving_generation_accurancy=False,
                 interest_rate=0.0542,
                 analyze_salib=True,
                 analyze_lhs=True,
                 analyze_industry=True,
                 analyze_household=False,
                 provider_price="average",
                 price_for_atypical_usage=False,
                 simulation_number_to_be_analyzed=None,
                 plot_strategy_industry=True,
                 plot_setup_heat_pump=True,
                 plot_setup_chp_gas_heater=True,
                 plot_peak_shaving_from_grid=False,
                 plot_strategy_over_100MWh_and_peak_shaving_into_grid=False,
                 plot_strategy_over_100MWh_and_self_consumption=False,
                 plot_strategy_Quarry_and_self_consumption=False,
                 plot_strategy_Metalworking_and_self_consumption=False,
                 plot_strategy_school_and_self_consumption=False,
                 plot_strategy_over_1000MWh_and_peak_shaving_from_grid_under_10=False,
                 plot_strategy_under_100MWh_and_peak_shaving_from_grid_under_10=False,

                 plot_strategy_over_100MWh_and_peak_shaving_into_grid_under_10=False,
                 plot_strategy_over_100MWh_and_peak_shaving_into_grid_over_50=False,
                 plot_strategy_over_100MWh_and_peak_shaving_into_grid_under_50=False):
        self.folder_name=folder_name
        self.start_date = start_date
        self.end_date = end_date
        self.json_file_name = json_file_name
        self.observation_period = observation_period
        self.pickle_file_name = pickle_file_name
        self.heat_map_precision_factor = heat_map_precision_factor
        self.interest_rate = interest_rate
        self.analyze_salib=analyze_salib
        self.analyze_lhs = analyze_lhs
        self.analyze_industry = analyze_industry
        self.analyze_household = analyze_household
        self.ElectricityPrices=ElectricityPricesConfig()
        self.BatteryData=BatteryDataConfig()
        self.provider_price=provider_price
        self.price_for_atypical_usage=price_for_atypical_usage
        self.simulation_number_to_be_analyzed=simulation_number_to_be_analyzed
        self.flags_plots ={"plot_heat_map": plot_heat_map}
        self.flags_houses = {"plot_all_houses": plot_all_houses,
                              "plot_sfh": plot_sfh,
                              "plot_mfh": plot_mfh}
        self.flags_strategy= {"plot_strategy_all": plot_strategy_all,
                              "plot_strategy_own_consumption": plot_strategy_own_consumption,
                              "plot_peak_shaving_from_grid":plot_peak_shaving_from_grid,
                              "plot_strategy_seasonal_storage": plot_strategy_seasonal_storage,
                              "plot_strategy_peak_shave_into_grid": plot_strategy_peak_shave_into_grid,
                              "plot_strategy_industry":plot_strategy_industry,
                              "plot_setup_heat_pump":plot_setup_heat_pump,
                              "plot_setup_chp_gas_heater":plot_setup_chp_gas_heater,
                              "plot_strategy_over_100MWh_and_peak_shaving_into_grid":plot_strategy_over_100MWh_and_peak_shaving_into_grid,
                              "plot_strategy_over_100MWh_and_self_consumption":plot_strategy_over_100MWh_and_self_consumption,
                              "plot_strategy_Quarry_and_self_consumption":plot_strategy_Quarry_and_self_consumption,
                              "plot_strategy_Metalworking_and_self_consumption":plot_strategy_Metalworking_and_self_consumption,
                              "plot_strategy_school_and_self_consumption":plot_strategy_school_and_self_consumption,
                              "plot_strategy_over_100MWh_and_peak_shaving_into_grid_under_10":plot_strategy_over_100MWh_and_peak_shaving_into_grid_under_10,
                              "plot_strategy_over_100MWh_and_peak_shaving_into_grid_over_50":plot_strategy_over_100MWh_and_peak_shaving_into_grid_over_50,
                              "plot_strategy_over_100MWh_and_peak_shaving_into_grid_under_50":plot_strategy_over_100MWh_and_peak_shaving_into_grid_under_50,
                              "plot_strategy_over_1000MWh_and_peak_shaving_from_grid_under_10" :plot_strategy_over_1000MWh_and_peak_shaving_from_grid_under_10,
                              "plot_strategy_under_100MWh_and_peak_shaving_from_grid_under_10" : plot_strategy_under_100MWh_and_peak_shaving_from_grid_under_10
                              }
        self.flags_components={"plot_battery_and_pv": plot_battery_and_pv,
                              "plot_h2_storage_relative_demand": plot_h2_storage_relative_demand,
                               "plot_h2_storage_relative_battery": plot_h2_storage_relative_battery,
                               "plot_peak_shaving_demand_accurancy": plot_peak_shaving_demand_accurancy,
                               "plot_peak_shaving_generation_accurancy": plot_peak_shaving_generation_accurancy,
                               "plot_net_present_value" : plot_net_present_value}
        self.flags_kpis={"plot_own_consumption":plot_own_consumption,
                         "plot_autarky":plot_autarky,
                         "plot_net_present_value": plot_net_present_value}
    def get_json_data(self,new_list,target_matrix):

        for a in  range(len(new_list)):
            newrow = []
            #soemtimes cfg isn't saved. idk why
            try :
                json.load(open(os.path.join(globals.HISIMPATH["results"], ""+str(new_list[a])+"/"+str(self.json_file_name)+".json")))
            except OSError:
                print("Error:not found: "+(os.path.join(globals.HISIMPATH["results"], ""+str(new_list[a])+"/"+str(self.json_file_name)+".json"))+"")
                continue
            json_data=json.load(open(os.path.join(globals.HISIMPATH["results"], ""+str(new_list[a])+"/"+str(self.json_file_name)+".json")))#
            newrow.append(json_data.get("Components", {}).get("Weather", {}).get("location", None ))
            if self.analyze_household:
                housetype = (json_data.get("Components", {}).get("CSVLoaderEL", {}).get("csv_filename", None))
                if "mfh" in housetype:
                    newrow.append("mfh")
                elif "sfh" in housetype:
                    newrow.append("sfh")
                else:
                    print("Error: not efh or mfh is the housetype")

            if self.analyze_industry:
                industry_type = (json_data.get("Components", {}).get("CSVLoaderEL", {}).get("column_name", None))
                if "Metalworking" in industry_type:
                    newrow.append("Metalworking")
                elif "development" in industry_type:
                    newrow.append("development")
                elif "Water treatment" in industry_type:
                    newrow.append("Water treatment")
                elif "Producing industry" in industry_type:
                    newrow.append("Producing industry")
                elif "Manufacturing industry" in industry_type:
                    newrow.append("Manufacturing industry")
                elif "Hotel" in industry_type:
                    newrow.append("Hotel")
                elif "Health care services" in industry_type:
                    newrow.append("Health care services")
                elif "Services" in industry_type:
                    newrow.append("Services")
                elif "Chemical industry" in industry_type:
                    newrow.append("Chemical industry")
                elif "Waste disposal" in industry_type:
                    newrow.append("Waste disposal")
                elif "Woodworking industry" in industry_type:
                    newrow.append("Woodworking industry")
                elif "Building materials" in industry_type:
                    newrow.append("Building materials")
                elif "Furniture retail" in industry_type:
                    newrow.append("Furniture retail")
                elif "Gravel" in industry_type:
                    newrow.append("Gravel")
                elif "Production" in industry_type:
                    newrow.append("Production")
                elif "Quarry" in industry_type:
                    newrow.append("Quarry")
                elif "Polymer processing" in industry_type:
                    newrow.append("Polymer processing")
                elif "Sawmill" in industry_type:
                    newrow.append("Sawmill")
                elif "Garden" in industry_type:
                    newrow.append("Garden")
                elif "School" in industry_type:
                    newrow.append("School")
                elif "(Pre-)School" in industry_type:
                    newrow.append("(Pre-)School")
                elif "Other" in industry_type:
                    newrow.append("Other")
                elif "Zoo" in industry_type:
                    newrow.append("Zoo")
                elif "Event hall" in industry_type:
                    newrow.append("Event hall")
                elif "Graveyard" in industry_type:
                    newrow.append("Graveyard")
                elif "Office building" in industry_type:
                    newrow.append("Office building")
                elif "Water pump" in industry_type:
                    newrow.append("Water pump")
                elif "Swimming Pool" in industry_type:
                    newrow.append("Swimming Pool")
                elif "Gym" in industry_type:
                    newrow.append("Gym")
                elif "Library" in industry_type:
                    newrow.append("Library")
                elif "Tunnel" in industry_type:
                    newrow.append("Tunnel")
                elif "Firefighters" in industry_type:
                    newrow.append("Firefighters")
                elif "Trailer park" in industry_type:
                    newrow.append("Trailer park")
                elif "Garage" in industry_type:
                    newrow.append("Garage")
                else:
                    if "eletrocplating" in (json_data.get("Components", {}).get("CSVLoaderEL", {}).get("csv_filename", None)):
                        newrow.append("eletcroplating")
                    elif "tool-manufacturer" in (json_data.get("Components", {}).get("CSVLoaderEL", {}).get("csv_filename", None)):
                        newrow.append("eletcroplating")
                    else:
                        print(industry_type+" is not listet. Therefore add it or postprocessing wont work")



            newrow.append(json_data.get("Components", {}).get("CSVLoaderWW", {}).get("multiplier", None ))
            newrow.append(json_data.get("Components", {}).get("CSVLoaderHW", {}).get("multiplier", None ))
            newrow.append(json_data.get("Components", {}).get("CSVLoaderEL", {}).get("multiplier", None ))
            newrow.append(json_data.get("Components", {}).get("PVSystem", {}).get("power", None ))
            newrow.append(json_data.get("Components", {}).get("AdvancedBattery", {}).get("capacity", None ))
            newrow.append(json_data.get("Components", {}).get("HeatPumpHplib", {}).get("p_th_set", None ))
            newrow.append(json_data.get("Components", {}).get("GasHeater", {}).get("power_max", None ))
            newrow.append(json_data.get("Components", {}).get("CHP", {}).get("p_el_max", None ))
            newrow.append(json_data.get("Components", {}).get("Electrolyzer", {}).get("power_electrolyzer", None ))
            newrow.append(json_data.get("Components", {}).get("HeatStorage", {}).get("V_SP_heating_water", None ))
            newrow.append(json_data.get("Components", {}).get("HeatStorage", {}).get("V_SP_warm_water", None ))
            newrow.append(json_data.get("Components", {}).get("HydrogenStorage", {}).get("max_capacity", None ))
            newrow.append(json_data.get("Components", {}).get("Controller", {}).get("strategy", None ))
            newrow.append(json_data.get("Components", {}).get("Controller", {}).get("percentage_to_shave", None ))
            newrow.append(json_data.get("Components", {}).get("Controller", {}).get("limit_to_shave", None))
            newrow.append(json_data.get("Components", {}).get("Weather", {}).get("simulation_number", None))

            target_matrix = np.vstack([target_matrix, newrow])
        return target_matrix


    def get_all_relevant_folders(self):
        folder_list=os.listdir(os.path.join(globals.HISIMPATH["results"]))
        new_list=[]
        start_date = int(self.start_date.replace("_", ""))
        end_date = int(self.end_date.replace("_", ""))
        a=0
        while a < len(folder_list):
            a=a+1
            if self.folder_name in folder_list[a-1]:
                split_string=folder_list[a-1].split("_",20)
                i=0
                while i < len(split_string):
                    if "industry" in split_string[i]:
                        split_string[i]="industry"
                    elif "household" in split_string[i]:
                        split_string[i] = "household"
                    i=i+1
                A="_".join(split_string)
                if "." in split_string[len(split_string)-1]:
                    variable = (A.replace(self.folder_name, "").replace(split_string[len(split_string)-1],"").replace("_", ""))
                    deleter=len(variable) -len(str(start_date))
                    if deleter>0:
                        variable=int(variable[deleter:])
                    else:
                        variable = int(variable)
                else:
                    variable=A.replace(self.folder_name,"").replace("_","")
                    variable = int(re.sub('\D', '', variable))
                if start_date <= variable and variable<=end_date:
                    new_list.append(folder_list[a-1])
        return new_list

    def get_pickle_informations(self,new_list,key_performance_indicators,target_matrix):
        b=0
        for a in  range(len(new_list)):
            newrow = []
            objects=[]

            #soemtimes pickle isn't saved. idk why
            try:
                with open((os.path.join(globals.HISIMPATH["results"],
                                        "" + str(new_list[a]) + "/" + str(self.pickle_file_name) + ".pkl")),
                          "rb") as openfile:
                    try:
                        objects.append(pickle.load(openfile))
                        b=b+1
                    except OSError:
                        print(self.pickle_file_name)
                    #Here starts Calculation of Parameters
                    A = (objects[0]['results'].T.T)
                    sum_Produced_Elect_pv= sum(A["PVSystem - ElectricityOutput [Electricity - W]"])
                    sum_Demand_Elect_house = sum(A[(A.filter(like="CSVLoaderEL").columns).values[0]])



                    my_post_processor = pp.PostProcessor(resultsdir=my_sim.resultsdir)
                    my_post_processor.run()



                    sum_Electricity_From_Grid=sum(x for x in A["Controller - ElectricityToOrFromGrid [Electricity - W]"] if x > 0)
                    sum_Electricity_Into_Grid = -sum(x for x in A["Controller - ElectricityToOrFromGrid [Electricity - W]"] if x < 0)
                    peak_from_grid=max(A["Controller - ElectricityToOrFromGrid [Electricity - W]"])
                    #sum electricity form Grid without Battery


                    if "AdvancedBattery - AC Battery Power [Electricity - W]" in A:
                        sum_Demand_Battery= sum(x for x in A["AdvancedBattery - AC Battery Power [Electricity - W]"] if x > 0)
                    else:
                        sum_Demand_Battery = 0
                    if "AdvancedBattery - AC Battery Power [Electricity - W]" in A:
                        sum_Produced_Elect_Battery= sum(x for x in A["AdvancedBattery - AC Battery Power [Electricity - W]"] if x < 0)
                    else:
                        sum_Produced_Elect_Battery = 0

                    if "HeatPumpHplib - ElectricalInputPower [Electricity - W]" in A:
                        sum_Demand_Elect_heat_pump= sum((A["HeatPumpHplib - ElectricalInputPower [Electricity - W]"]))
                    else:
                        sum_Demand_Elect_heat_pump = 0

                    if "Electrolyzer - Unused Power [Electricity - W]" in A:
                        sum_Demand_Elect_electrolyzer= sum((A["Controller - ElectricityToElectrolyzerTarget [Electricity - W]"])) - sum((A["Electrolyzer - Unused Power [Electricity - W]"]))

                    else:
                        sum_Demand_Elect_electrolyzer = 0

                    if "CHP - ElectricityOutput [Electricity - W]" in A:
                        sum_Produced_Elect_chp= sum((A["CHP - ElectricityOutput [Electricity - W]"]))
                    else:
                        sum_Produced_Elect_chp = 0

                    if "CHP - ElectricityOutput [Electricity - W]" in A:
                        sum_Produced_Elect_chp= sum((A["CHP - ElectricityOutput [Electricity - W]"]))
                    else:
                        sum_Produced_Elect_chp = 0

                    if "CHP - ElectricityOutput [Electricity - W]" in A:
                        sum_Produced_Elect_chp= sum((A["CHP - ElectricityOutput [Electricity - W]"]))
                    else:
                        sum_Produced_Elect_chp = 0

                    sum_battery_loss=0
                    length=A["AdvancedBattery - AC Battery Power [Electricity - W]"].size
                    i=0
                    sum_Electricity_From_Grid_without_battery=0
                    sum_Electricity_Into_Grid_without_battery=0
                    sum_Electricity_From_Grid_with_battery_test=0
                    sum_Electricity_Into_Grid_with_battery_test=0
                    peak_from_grid_without_battery=0
                    while i < length:
                        variable=0
                        variable= A["PVSystem - ElectricityOutput [Electricity - W]"][i] - A[(A.filter(like="CSVLoaderEL").columns).values[0]][i]
                        if "HeatPumpHplib - ElectricalInputPower [Electricity - W]" in A:
                            variable= variable - A["HeatPumpHplib - ElectricalInputPower [Electricity - W]"][i]
                        if "Electrolyzer - Unused Power [Electricity - W]" not in A:
                            if "CHP - ElectricityOutput [Electricity - W]" in A:
                                variable= variable + A["CHP - ElectricityOutput [Electricity - W]"][i]
                        else:
                            if "CHP - ElectricityOutput [Electricity - W]" in A:
                                variable_test= variable + A["CHP - ElectricityOutput [Electricity - W]"][i]
                        if "AdvancedBattery - AC Battery Power [Electricity - W]" in A:
                            variable_test = variable_test - A["AdvancedBattery - AC Battery Power [Electricity - W]"][i]


                        if variable < 0:
                            sum_Electricity_From_Grid_without_battery= sum_Electricity_From_Grid_without_battery - variable
                            if -variable > peak_from_grid_without_battery:
                                peak_from_grid_without_battery = -variable
                        elif  variable > 0:
                            sum_Electricity_Into_Grid_without_battery= sum_Electricity_Into_Grid_without_battery + variable

                        if variable_test < 0:
                            sum_Electricity_From_Grid_with_battery_test= sum_Electricity_From_Grid_with_battery_test - variable_test
                            if -variable > peak_from_grid_without_battery:
                                peak_from_grid_without_battery = -variable
                        elif  variable_test > 0:
                            sum_Electricity_Into_Grid_with_battery_test= sum_Electricity_Into_Grid_with_battery_test + variable_test

                        i = i + 1
                    sum_Electricity_Into_Grid=sum_Electricity_Into_Grid_with_battery_test
                    sum_Electricity_From_Grid=sum_Electricity_From_Grid_with_battery_test
                    sum_Demand=sum_Demand_Elect_heat_pump+sum_Demand_Elect_house+sum_Demand_Elect_electrolyzer+sum_Demand_Battery

                    sum_Produced=sum_Produced_Elect_pv+sum_Produced_Elect_Battery+sum_Produced_Elect_chp

                    a=sum_Demand_Elect_house-sum_Produced_Elect_pv+sum_Demand_Battery-sum_Produced_Elect_Battery
                    own_consumption=(sum_Produced_Elect_pv-sum_Electricity_Into_Grid)/(sum_Produced_Elect_pv)
                    autarky=(sum_Demand - sum_Electricity_From_Grid) / (sum_Demand)

                    own_consumption=(sum_Produced-sum_Electricity_Into_Grid)/sum_Produced

                    bat_size=target_matrix[b,6]#kwh
                    cost_bat=(1374.6 * bat_size ** (-0.203))* bat_size
                    cost_bat_low=(500* bat_size ** (-0.143))* bat_size

                    pv_size=target_matrix[b,5] #kW
                    if pv_size == None:
                        pv_size=0
                        cost_pv=0
                    else:
                        pv_size = target_matrix[b, 5] / 1000
                        cost_pv=(2095.8 * pv_size ** (-0.166))* pv_size

                    chp_size=target_matrix[b,9] #kW
                    if chp_size == None:
                        chp_size=0
                        cost_chp=0
                        cost_chp_low=0
                    else:
                        chp_size = target_matrix[b, 9] / 1000
                        cost_chp=(25689 * chp_size ** (-0.581))* chp_size
                        cost_chp_low=(6000 * chp_size ** (-0.5))* chp_size


                    h2_storage_size=target_matrix[b,13] #in liters, need to be changed into MWH!!
                    if h2_storage_size == None:
                        h2_storage_size=0
                        cost_h2_storage=0
                        cost_h2_storage_low=0
                    else:
                        h2_storage_size = target_matrix[b, 13] *33.33/1000
                        cost_h2_storage = (14990 * h2_storage_size ** (-0.079)) * h2_storage_size
                        cost_h2_storage_low = (11000 * h2_storage_size ** (-0.075)) * h2_storage_size

                    electrolzer_size=target_matrix[b,10]#in liters, need to be changed into MWH!!
                    if electrolzer_size == None:
                        electrolzer_size=0
                        cost_chp=0
                        cost_chp_low=0
                        cost_electrolyzer=0
                        cost_electrolyzer_low=0
                    else:
                        electrolzer_size = target_matrix[b, 10]
                        cost_electrolyzer = (5012.9 * electrolzer_size ** (-0.054)) * electrolzer_size
                        cost_electrolyzer_low = (1000 * electrolzer_size ** (-0.02)) * electrolzer_size



                    electricity_prize_into_grid = self.ElectricityPrices.electricity_price_relative_to_pv_size(pv_size=pv_size)

                    utilisation_hours_with_battery = sum_Electricity_From_Grid/peak_from_grid
                    utilisation_hours_without_battery = sum_Electricity_From_Grid_without_battery/peak_from_grid_without_battery

                    cost_total_investment= cost_bat + cost_chp + cost_h2_storage + cost_electrolyzer
                    cost_total_investment_low=cost_bat_low+ cost_chp_low+cost_h2_storage_low+cost_electrolyzer_low
                    ElectricityPrices=ElectricityPricesConfig()
                    if self.analyze_household==True:
                        list_electricity_price_from_grid_household=ElectricityPrices.calculate_electricity_price_from_grid_household(observation_period=int(self.observation_period))
                        cashflows_with_battery=[]
                        cashflows_with_battery_low = []
                        cashflows_without_battery=[]
                        cashflows_with_battery.append(-cost_total_investment)
                        cashflows_with_battery_low.append(-cost_total_investment_low)
                        cashflows_without_battery.append(0)
                        for price in list_electricity_price_from_grid_household:
                            income_delta = (0.25 / 1000) * (
                                        -sum_Electricity_From_Grid * price + sum_Electricity_Into_Grid * electricity_prize_into_grid)

                            income_delta_without_battery = (0.25 / 1000) * (
                                        -sum_Electricity_From_Grid_without_battery * price + sum_Electricity_Into_Grid_without_battery * electricity_prize_into_grid)
                            cashflows_with_battery.append(income_delta)
                            cashflows_with_battery_low.append(income_delta)
                            cashflows_without_battery.append(income_delta_without_battery)

                    elif self.analyze_industry==True:
                        leistungspreis_with_battery_low, arbeitspreis_with_battery_low = self.ElectricityPrices.calculate_electricity_price_from_grid_industry(utilisation_hours=utilisation_hours_with_battery,provider_price="low",price_for_atypical_usage=self.price_for_atypical_usage,observation_period=self.observation_period)
                        leistungspreis_with_battery_average, arbeitspreis_with_battery_average = self.ElectricityPrices.calculate_electricity_price_from_grid_industry(utilisation_hours=utilisation_hours_with_battery,provider_price="average",price_for_atypical_usage=self.price_for_atypical_usage,observation_period=self.observation_period)
                        leistungspreis_with_battery_high, arbeitspreis_with_battery_high = self.ElectricityPrices.calculate_electricity_price_from_grid_industry(utilisation_hours=utilisation_hours_with_battery,provider_price="high",price_for_atypical_usage=self.price_for_atypical_usage,observation_period=self.observation_period)

                        leistungspreis_without_battery_low, arbeitspreis_without_battery_low, = self.ElectricityPrices.calculate_electricity_price_from_grid_industry(utilisation_hours=utilisation_hours_without_battery,provider_price="low",price_for_atypical_usage=self.price_for_atypical_usage,observation_period=self.observation_period)
                        leistungspreis_without_battery_average, arbeitspreis_without_battery_average = self.ElectricityPrices.calculate_electricity_price_from_grid_industry(utilisation_hours=utilisation_hours_without_battery,provider_price="average",price_for_atypical_usage=self.price_for_atypical_usage,observation_period=self.observation_period)
                        leistungspreis_without_battery_high, arbeitspreis_without_battery_high = self.ElectricityPrices.calculate_electricity_price_from_grid_industry(utilisation_hours=utilisation_hours_without_battery,provider_price="high",price_for_atypical_usage=self.price_for_atypical_usage,observation_period=self.observation_period)



                        cashflows_with_battery=[]
                        cashflows_with_battery_low = []
                        cashflows_with_battery_high = []
                        cashflows_with_battery.append(-cost_total_investment)
                        cashflows_with_battery_low.append(-cost_total_investment)
                        cashflows_with_battery_high.append(-cost_total_investment)

                        cashflows_without_battery=[]
                        cashflows_without_battery_low = []
                        cashflows_without_battery_high = []
                        cashflows_without_battery.append(0)
                        cashflows_without_battery_low.append(0)
                        cashflows_without_battery_high.append(0)

                        counter=0
                        while counter <= self.observation_period:
                            electricity_prize_from_grid_wtih_battery_low = leistungspreis_with_battery_low[counter] * peak_from_grid / 1000 + arbeitspreis_with_battery_low[counter] * sum_Electricity_From_Grid * 0.25 / 1000
                            electricity_prize_from_grid_wtih_battery_average = leistungspreis_with_battery_average[counter] * peak_from_grid / 1000 + arbeitspreis_with_battery_average[counter] * sum_Electricity_From_Grid * 0.25 / 1000
                            electricity_prize_from_grid_wtih_battery_high = leistungspreis_with_battery_high[counter] * peak_from_grid / 1000 + arbeitspreis_with_battery_high[counter] * sum_Electricity_From_Grid * 0.25 / 1000

                            electricity_prize_from_grid_wtihout_battery_low = leistungspreis_without_battery_low[counter] * peak_from_grid_without_battery / 1000 + arbeitspreis_without_battery_low[counter] * sum_Electricity_From_Grid_without_battery * 0.25 / 1000
                            electricity_prize_from_grid_wtihout_battery_average = leistungspreis_without_battery_average[counter] * peak_from_grid_without_battery / 1000 + arbeitspreis_without_battery_average[counter] * sum_Electricity_From_Grid_without_battery * 0.25 / 1000
                            electricity_prize_from_grid_wtihout_battery_high = leistungspreis_without_battery_high[counter] * peak_from_grid_without_battery / 1000 + arbeitspreis_without_battery_high[counter] * sum_Electricity_From_Grid_without_battery * 0.25 / 1000


                            electricity_prize_from_grid_wtih_battery_low = electricity_prize_from_grid_wtih_battery_low + 0.8 * 0.21 * sum_Electricity_From_Grid * 0.25 / 1000
                            electricity_prize_from_grid_wtih_battery_average = electricity_prize_from_grid_wtih_battery_average + 0.8 * 0.21 * sum_Electricity_From_Grid * 0.25 / 1000
                            electricity_prize_from_grid_wtih_battery_high = electricity_prize_from_grid_wtih_battery_high + 0.8 * 0.21 * sum_Electricity_From_Grid * 0.25 / 1000

                            electricity_prize_from_grid_wtihout_battery_low = electricity_prize_from_grid_wtihout_battery_low + 0.8 * 0.21 * sum_Electricity_From_Grid_without_battery * 0.25 / 1000
                            electricity_prize_from_grid_wtihout_battery_average = electricity_prize_from_grid_wtihout_battery_average + 0.8 * 0.21 * sum_Electricity_From_Grid_without_battery * 0.25 / 1000
                            electricity_prize_from_grid_wtihout_battery_high = electricity_prize_from_grid_wtihout_battery_high + 0.8 * 0.21 * sum_Electricity_From_Grid_without_battery * 0.25 / 1000

                            income_delta_low = (-electricity_prize_from_grid_wtih_battery_low + sum_Electricity_Into_Grid / 1000 * 0.25 * electricity_prize_into_grid)
                            income_delta_average = (-electricity_prize_from_grid_wtih_battery_average + sum_Electricity_Into_Grid / 1000 * 0.25 * electricity_prize_into_grid)
                            income_delta_high = (-electricity_prize_from_grid_wtih_battery_high + sum_Electricity_Into_Grid / 1000 * 0.25 * electricity_prize_into_grid)

                            income_delta_without_battery_low = (-electricity_prize_from_grid_wtihout_battery_low + sum_Electricity_Into_Grid_without_battery / 1000 * 0.25 * electricity_prize_into_grid)
                            income_delta_without_battery_average = (-electricity_prize_from_grid_wtihout_battery_average + sum_Electricity_Into_Grid_without_battery / 1000 * 0.25 * electricity_prize_into_grid)
                            income_delta_without_battery_high = (-electricity_prize_from_grid_wtihout_battery_high + sum_Electricity_Into_Grid_without_battery / 1000 * 0.25 * electricity_prize_into_grid)

                            cashflows_with_battery.append(income_delta_average)
                            cashflows_with_battery_low.append(income_delta_low)
                            cashflows_with_battery_high.append(income_delta_high)

                            cashflows_without_battery.append(income_delta_without_battery_average)
                            cashflows_without_battery_low.append(income_delta_without_battery_low)
                            cashflows_without_battery_high.append(income_delta_without_battery_high)

                            counter = counter + 1


                    if self.analyze_household==True and self.analyze_industry==True:
                        print("try to analayze household and industry-->not working therfore change default values")
                        income_delta = (0.25 / 1000) * (-sum_Electricity_From_Grid * electricity_prize_from_grid_wtih_battery + sum_Electricity_Into_Grid * electricity_prize_into_grid)
                        income_delta_without_battery = (0.25 / 1000) * (-sum_Electricity_From_Grid_without_battery * electricity_prize_from_grid_wtihout_battery + sum_Electricity_Into_Grid_without_battery * electricity_prize_into_grid)

                    ###Net presentvalue with battery
                    if self.analyze_household == True:
                        net_present_value_with_battery=npf.npv(self.interest_rate, cashflows_with_battery).round(2)
                        net_present_value_with_battery_low=npf.npv(self.interest_rate, cashflows_with_battery_low).round(2)

                        net_present_value_without_battery=npf.npv(self.interest_rate, cashflows_without_battery).round(2)

                        ###Delta of net present values
                        delta_net_present_value= +net_present_value_with_battery - net_present_value_without_battery
                        delta_net_present_value_low= +net_present_value_with_battery_low - net_present_value_without_battery

                        return_of_investment= (delta_net_present_value - cost_total_investment)/cost_total_investment
                        return_of_investment_low= (delta_net_present_value_low - cost_total_investment_low)/cost_total_investment_low


                        pay_back_duration= cost_total_investment/(-np.mean(cashflows_without_battery[1:])+np.mean(cashflows_with_battery[1:]))
                        pay_back_duration_low= cost_total_investment_low/(-np.mean(cashflows_without_battery[1:])+np.mean(cashflows_with_battery_low[1:]))
                        delta_net_present_value_high=0
                        return_of_investment_high=0
                        pay_back_duration_high=0

                    if self.analyze_industry == True:
                        net_present_value_with_battery=npf.npv(self.interest_rate, cashflows_with_battery).round(2)
                        net_present_value_with_battery_low=npf.npv(self.interest_rate, cashflows_with_battery_low).round(2)
                        net_present_value_with_battery_high=npf.npv(self.interest_rate, cashflows_with_battery_high).round(2)

                        net_present_value_without_battery = npf.npv(self.interest_rate, cashflows_without_battery).round(2)
                        net_present_value_without_battery_low = npf.npv(self.interest_rate,cashflows_without_battery_low).round(2)
                        net_present_value_without_battery_high = npf.npv(self.interest_rate,cashflows_without_battery_high).round(2)

                        delta_net_present_value= +net_present_value_with_battery - net_present_value_without_battery
                        delta_net_present_value_low= +net_present_value_with_battery_low - net_present_value_without_battery_low
                        delta_net_present_value_high= +net_present_value_with_battery_high - net_present_value_without_battery_high

                        return_of_investment= (delta_net_present_value - cost_total_investment)/cost_total_investment
                        return_of_investment_low= (delta_net_present_value_low - cost_total_investment)/cost_total_investment
                        return_of_investment_high = (delta_net_present_value_high - cost_total_investment) / cost_total_investment

                        pay_back_duration = cost_total_investment / (-np.mean(cashflows_without_battery[1:]) + np.mean(cashflows_with_battery[1:]))
                        pay_back_duration_low = cost_total_investment / (
                                    -np.mean(cashflows_without_battery_low[1:]) + np.mean(cashflows_with_battery_low[1:]))
                        pay_back_duration_high = cost_total_investment / (
                                    -np.mean(cashflows_without_battery_high[1:]) + np.mean(cashflows_with_battery_high[1:]))

                    full_cycles=((-sum_Produced_Elect_Battery+sum_Demand_Battery)*0.25/1000)/(2*bat_size)
                    delta_utilisation_hours = utilisation_hours_with_battery - utilisation_hours_without_battery

                    if own_consumption > 1:
                        print("owncumption is bigger than one :" +str(own_consumption))
                        own_consumption=1
                    elif own_consumption <  0:
                        print("owncumption is smaller than one :" + str(own_consumption))
                        own_consumption=0.001
                    if autarky > 1:
                        print("autarky is bigger than one :" +str(autarky))
                        autarky=1
                    elif autarky <  0:
                        print("autarky is smaller than one :" + str(autarky))
                        autarky=0.001
                    electricity_demand_building = sum_Demand_Elect_house * 0.25 / 1000
                    newrow.append(own_consumption) #own_consumption
                    newrow.append(autarky) #autarky
                    newrow.append(full_cycles)
                    newrow.append(delta_net_present_value)
                    newrow.append(delta_net_present_value_low)
                    newrow.append(delta_net_present_value_high)
                    newrow.append(return_of_investment) #autarky
                    newrow.append(return_of_investment_low)
                    newrow.append(return_of_investment_high)
                    newrow.append(pay_back_duration)
                    newrow.append(pay_back_duration_low)
                    newrow.append(pay_back_duration_high)
                    newrow.append(utilisation_hours_with_battery)
                    newrow.append(delta_utilisation_hours)
                    newrow.append(electricity_demand_building)
                    key_performance_indicators = np.vstack([key_performance_indicators, newrow])

            except OSError:
                print("Error:not found: "+(os.path.join(globals.HISIMPATH["results"], ""+str(new_list[a])+"/"+str(self.pickle_file_name)+".pickle"))+"")
                continue
        return key_performance_indicators


    def transform_data_for_plot(self,target_matrix,key_performance_indicators,kpi,component):
        breaker=False
        num_rows, num_cols = target_matrix.shape
        if num_rows ==1:
            breaker=True
            return 0, 0 ,0, breaker
        x = 0
        x_axis = []
        y_axis = []
        own_consumption = []
        autarky = []
        if self.analyze_industry == True:

            while x < (num_rows - 1):
                x = x + 1
                annual_demand = (float(key_performance_indicators[x, 16]) / 1000)
                if component in "plot_battery_and_pv":
                    x_axis.append((target_matrix[x, 5] / 1000) / (float(key_performance_indicators[x,16])/1000))  # in kW/kW
                    y_axis.append(target_matrix[x, 6] / (float(key_performance_indicators[x,16])/1000))  # in kWh/kw
                elif component in "plot_net_present_value":
                    x_axis.append((target_matrix[x, 5] / 1000) / (float(key_performance_indicators[x,16])/1000))  # in kW/kW
                    y_axis.append(target_matrix[x, 6] / (float(key_performance_indicators[x,16])/1000))  # in kWh/kw

                elif component in "plot_h2_storage_relative_demand":
                    if target_matrix[x, 13] == None or target_matrix[x, 13] == 0:
                        breaker = True
                        return 1, 0 ,0, breaker
                    else:
                        x_axis.append((target_matrix[x, 5]/1000) / target_matrix[x, 6])  # in kW/kW
                        y_axis.append(target_matrix[x, 13]/(target_matrix[x, 4])) # in kWh/kw
                elif component in "plot_h2_storage_relative_battery":
                    if target_matrix[x, 13] == None or target_matrix[x, 13] == 0:
                        breaker = True
                        return 1, 0 ,0, breaker
                    else:
                        x_axis.append((target_matrix[x, 5]/1000) / target_matrix[x, 4])  # in kW/kW
                        y_axis.append(target_matrix[x, 13]/(target_matrix[x, 6])) # in kWh/kw
                elif component in "plot_peak_shaving_generation_accurancy":
                    print("stop")

                else:
                    print("no component to print choosed")
                    return 1, 0, 0, breaker
        elif self.analyze_household==True:
            while x < (num_rows - 1):
                x = x + 1
                if component in "plot_battery_and_pv":
                    x_axis.append((target_matrix[x, 5] / 1000) / target_matrix[x, 4])  # in kW/kW
                    y_axis.append(target_matrix[x, 6] / (target_matrix[x, 4]))  # in kWh/kw
                elif component in "plot_net_present_value":
                    x_axis.append((target_matrix[x, 5] / 1000) / target_matrix[x, 4])  # in kW/kW
                    y_axis.append(target_matrix[x, 6] / (target_matrix[x, 4]))  # in kWh/kw

                elif component in "plot_h2_storage_relative_demand":
                    if target_matrix[x, 13] == None or target_matrix[x, 13] == 0:
                        breaker = True
                        return 1, 0 ,0, breaker
                    else:
                        x_axis.append((target_matrix[x, 5]/1000) / target_matrix[x, 6])  # in kW/kW
                        y_axis.append(target_matrix[x, 13]/(target_matrix[x, 4])) # in kWh/kw
                elif component in "plot_h2_storage_relative_battery":
                    if target_matrix[x, 13] == None or target_matrix[x, 13] == 0:
                        breaker = True
                        return 1, 0 ,0, breaker
                    else:
                        x_axis.append((target_matrix[x, 5]/1000) / target_matrix[x, 4])  # in kW/kW
                        y_axis.append(target_matrix[x, 13]/(target_matrix[x, 6])) # in kWh/kw
                elif component in "plot_peak_shaving_generation_accurancy":
                    print("stop")

                else:
                    print("no component to print choosed")
                    return 1, 0, 0, breaker
        x_axis = np.around(np.array(x_axis), decimals=2)
        y_axis = np.around(np.array(y_axis), decimals=2)
        if kpi == "OwnConsumption":
            key_to_look_at = key_performance_indicators[1::, 0]
        elif kpi == "Autarky":
            key_to_look_at = key_performance_indicators[1::, 1]
        elif kpi == "NetPresentValue":
            key_to_look_at = key_performance_indicators[1::, 2]
        elif kpi == "DeltaNetPresentValue":
            key_to_look_at = key_performance_indicators[1::, 3]
        elif kpi == "DeltaNetPresentValueLow":
            key_to_look_at = key_performance_indicators[1::, 4]
        elif kpi == "DeltaNetPresentValueHigh":
            key_to_look_at = key_performance_indicators[1::, 5]

        # Set up Matrix and fill with values-Has to be done bec. of Latin Hypercube design
        plot_boundaries = [[((min(x_axis))), (max(x_axis))],
                           [(min(y_axis)), (max(y_axis))]]
        precision_x_axis = (plot_boundaries[(0)][1] - plot_boundaries[(0)][0]) / self.heat_map_precision_factor
        precision_y_axis = (plot_boundaries[(1)][1] - plot_boundaries[(1)][0]) / self.heat_map_precision_factor
        grid = np.empty([self.heat_map_precision_factor+1, self.heat_map_precision_factor+1])
        grid[:]=np.nan
        x = 0
        if (len(x_axis)) ==1:
            breaker=True
            return 0, 0 ,0, breaker
        while x < (len(x_axis)):

            x_index = round((x_axis[x] - plot_boundaries[(0)][0]) / precision_x_axis)
            y_index = round((y_axis[x] - plot_boundaries[(1)][0]) / precision_y_axis)



            if math.isnan(grid[y_index, x_index]):
                grid[y_index, x_index] = float(key_to_look_at[x])
            else:
                grid[y_index, x_index] = ((grid[y_index, x_index]) + float(key_to_look_at[x]))/ 2
            x = x + 1
        Z =grid
        precision_x_axis = (-np.round(plot_boundaries[(0)][0],1) + np.round(plot_boundaries[(0)][1],1)) / (self.heat_map_precision_factor+1)
        precision_y_axis = (-np.round(plot_boundaries[(1)][0],1)+ np.round(plot_boundaries[(1)][1],1)) / (self.heat_map_precision_factor+1)
        x= np.arange (np.round(plot_boundaries[(0)][0],1), np.round(plot_boundaries[(0)][1],1), precision_x_axis)
        y= np.arange (np.round(plot_boundaries[(1)][0],1), np.round(plot_boundaries[(1)][1],1), precision_y_axis)
        '''
        if len(x)> len(Z)+1:
            x = np.arange(plot_boundaries[(0)][0], plot_boundaries[(0)][1], precision_x_axis)
        if len(x)<= len(Z)+1:
            x = np.arange(plot_boundaries[(0)][0], plot_boundaries[(0)][1]+precision_x_axis-precision_x_axis/10, precision_x_axis)
        if len(y) > len(Z) + 1:
            y = np.arange(plot_boundaries[(1)][0], plot_boundaries[(1)][1], precision_y_axis)
        '''
        return Z, x, y, breaker


    def sort_out_because_of_house_choosing(self,target_matrix,key_performance_indicators,x ):
        breaker= False
        if x=="plot_all_houses":
            target_matrix_new = target_matrix
            key_performance_indicators_new = key_performance_indicators
        elif x=="plot_sfh":
            target_matrix_new = np.delete(target_matrix, np.where(target_matrix == "mfh")[0], 0)
            key_performance_indicators_new = np.delete(key_performance_indicators,
                                                       np.where(target_matrix == "mfh")[0], 0)

        elif x=="plot_mfh":
            target_matrix_new = np.delete(target_matrix, np.where(target_matrix == "sfh")[0], 0)
            key_performance_indicators_new = np.delete(key_performance_indicators,
                                                       np.where(target_matrix == "sfh")[0], 0)
        else:
            breaker= True
            return 0 , 0 , breaker
        return target_matrix_new, key_performance_indicators_new, breaker
    def sort_out_because_of_strategy_choosing(self,target_matrix,key_performance_indicators,y):
        breaker= False
        if y=="plot_strategy_all":
            target_matrix_new = target_matrix.copy()
            key_performance_indicators_new = key_performance_indicators.copy()
        elif y=="plot_strategy_own_consumption":

            B =(target_matrix[np.any(target_matrix == "Weather", axis=1)])
            A = (target_matrix[np.any(target_matrix == "optimize_own_consumption", axis=1)])
            target_matrix_new=np.append(B,A,axis=0)

            C = key_performance_indicators.copy()
            i=0
            while i < (len(target_matrix[:,14])-1):
                i=i+1
                if target_matrix[i,14] != "optimize_own_consumption":
                    C[i,0] = "delete"
            key_performance_indicators_new = np.delete(C, np.where(C == "delete")[0], 0)
        elif y == "plot_peak_shaving_from_grid":
            B =(target_matrix[np.any(target_matrix == "Weather", axis=1)])
            A = (target_matrix[np.any(target_matrix == "peak_shaving_from_grid", axis=1)])
            target_matrix_new=np.append(B,A,axis=0)

            C = key_performance_indicators.copy()
            i=0
            while i < (len(target_matrix[:,14])-1):
                i=i+1
                if target_matrix[i,14] != "peak_shaving_from_grid":
                    C[i,0] = "delete"
            key_performance_indicators_new = np.delete(C, np.where(C == "delete")[0], 0)




        elif y=="plot_strategy_seasonal_storage":

            B =(target_matrix[np.any(target_matrix == "Weather", axis=1)])
            A = (target_matrix[np.any(target_matrix == "seasonal_storage", axis=1)])
            target_matrix_new=np.append(B,A,axis=0)
            key_performance_indicators_new=key_performance_indicators.copy()
            i=0
            while i < (len(target_matrix[:,14])-1):
                i=i+1
                if target_matrix[i,14] != "seasonal_storage":
                    key_performance_indicators_new[i,0] = "delete"

            key_performance_indicators_new = np.delete(key_performance_indicators_new, np.where(key_performance_indicators_new == "delete")[0], 0)

        elif y == "plot_strategy_school_and_self_consumption":
            x = 0
            target_matrix_new = target_matrix[0, :]
            key_performance_indicators_new = key_performance_indicators[0, :]
            while x < target_matrix.shape[0] - 1:
                x = x + 1

                if x == 1:
                    target_matrix_new = np.row_stack((target_matrix_new, target_matrix[x, :]))
                    key_performance_indicators_new = np.row_stack((key_performance_indicators_new, key_performance_indicators[x, :]))
                    continue
                if target_matrix[x, 1] == "School" and target_matrix[x,14] != "optimize_own_consumption" and ((key_performance_indicators[x,2:6].astype(float)>-20000).any() == True):
                    target_matrix_new = np.row_stack((target_matrix_new, target_matrix[x, :]))
                    key_performance_indicators_new = np.row_stack((key_performance_indicators_new, key_performance_indicators[x, :]))
                    continue

        elif y == "plot_setup_heat_pump":
            x = 0
            target_matrix_new = target_matrix[0, :]
            key_performance_indicators_new = key_performance_indicators[0, :]
            while x < target_matrix.shape[0] - 1:
                x = x + 1

                if x == 1:
                    target_matrix_new = np.row_stack((target_matrix_new, target_matrix[x, :]))
                    key_performance_indicators_new = np.row_stack((key_performance_indicators_new, key_performance_indicators[x, :]))
                    continue
                if str(target_matrix[x,7]) != "None":
                    target_matrix_new = np.row_stack((target_matrix_new, target_matrix[x, :]))
                    key_performance_indicators_new = np.row_stack((key_performance_indicators_new, key_performance_indicators[x, :]))
                    continue
        elif y == "plot_setup_chp_gas_heater":
            x = 0
            target_matrix_new = target_matrix[0, :]
            key_performance_indicators_new = key_performance_indicators[0, :]
            while x < target_matrix.shape[0] - 1:
                x = x + 1

                if x == 1:
                    target_matrix_new = np.row_stack((target_matrix_new, target_matrix[x, :]))
                    key_performance_indicators_new = np.row_stack(
                        (key_performance_indicators_new, key_performance_indicators[x, :]))
                    continue
                if str(target_matrix[x, 9]) != "None":
                    target_matrix_new = np.row_stack((target_matrix_new, target_matrix[x, :]))
                    key_performance_indicators_new = np.row_stack(
                        (key_performance_indicators_new, key_performance_indicators[x, :]))
                    continue

        elif self.analyze_industry==True:

            B =(target_matrix[np.any(target_matrix == "Weather", axis=1)])
            A = (target_matrix[np.any(target_matrix == "peak_shaving_from_grid", axis=1)])
            target_matrix_new=np.append(B,A,axis=0)

            C = key_performance_indicators.copy()
            i=0
            while i < (len(target_matrix[:,14])-1):
                i=i+1
                if target_matrix[i,14] != "peak_shaving_from_grid":
                    C[i,0] = "delete"
            key_performance_indicators_new = np.delete(C, np.where(C == "delete")[0], 0)
            if y == "plot_strategy_Metalworking_and_self_consumption":
                x = 0
                target_matrix_new = target_matrix[0, :]
                key_performance_indicators_new = key_performance_indicators[0, :]
                while x < target_matrix.shape[0] - 1:
                    x = x + 1

                    if x == 1:
                        target_matrix_new = np.row_stack((target_matrix_new, target_matrix[x, :]))
                        key_performance_indicators_new = np.row_stack((key_performance_indicators_new, key_performance_indicators[x, :]))
                        continue
                    if target_matrix[x, 1] == "Metalworking" and target_matrix[x,14] != "optimize_own_consumption" and ((key_performance_indicators[x,2:6].astype(float)>-20000).any() == True):
                        target_matrix_new = np.row_stack((target_matrix_new, target_matrix[x, :]))
                        key_performance_indicators_new = np.row_stack((key_performance_indicators_new, key_performance_indicators[x, :]))
                        continue
            elif y == "plot_strategy_Quarry_and_self_consumption":
                x = 0
                target_matrix_new = target_matrix[0, :]
                key_performance_indicators_new = key_performance_indicators[0, :]
                while x < target_matrix.shape[0] - 1:
                    x = x + 1

                    if x == 1:
                        target_matrix_new = np.row_stack((target_matrix_new, target_matrix[x, :]))
                        key_performance_indicators_new = np.row_stack((key_performance_indicators_new, key_performance_indicators[x, :]))
                        continue
                    if target_matrix[x, 1] == "Quarry" and target_matrix[x,14] != "optimize_own_consumption" and ((key_performance_indicators[x,2:6].astype(float)>-20000).any() == True):
                        target_matrix_new = np.row_stack((target_matrix_new, target_matrix[x, :]))
                        key_performance_indicators_new = np.row_stack((key_performance_indicators_new, key_performance_indicators[x, :]))
                        continue

            elif y == "plot_strategy_over_100MWh_and_self_consumption":
                x = 0
                target_matrix_new = target_matrix[0, :]
                key_performance_indicators_new = key_performance_indicators[0, :]
                while x < target_matrix.shape[0] - 1:
                    x = x + 1

                    if x == 1:
                        target_matrix_new = np.row_stack((target_matrix_new, target_matrix[x, :]))
                        key_performance_indicators_new = np.row_stack((key_performance_indicators_new, key_performance_indicators[x, :]))
                        continue
                    if float(key_performance_indicators[x,7])/1000>100   and target_matrix[x,14] != "optimize_own_consumption" and ((key_performance_indicators[x,2:6].astype(float)>-20000).any() == True):
                        target_matrix_new = np.row_stack((target_matrix_new, target_matrix[x, :]))
                        key_performance_indicators_new = np.row_stack((key_performance_indicators_new, key_performance_indicators[x, :]))
                        continue
            elif y == "plot_strategy_over_100MWh_and_peak_shaving_into_grid_over_50":
                x = 0
                target_matrix_new = target_matrix[0, :]
                key_performance_indicators_new = key_performance_indicators[0, :]
                while x < target_matrix.shape[0] - 1:
                    x = x + 1

                    if x == 1:
                        target_matrix_new = np.row_stack((target_matrix_new, target_matrix[x, :]))
                        key_performance_indicators_new = np.row_stack((key_performance_indicators_new, key_performance_indicators[x, :]))
                        continue
                    if float(key_performance_indicators[x,7])/1000>100   and target_matrix[x,14] != "peak_shaving_from_grid" and float(target_matrix[x,15]) >0.5 and ((key_performance_indicators[x,2:6].astype(float)>-20000).any() == True):
                        target_matrix_new = np.row_stack((target_matrix_new, target_matrix[x, :]))
                        key_performance_indicators_new = np.row_stack((key_performance_indicators_new, key_performance_indicators[x, :]))
                        continue
            elif y == "plot_strategy_over_100MWh_and_peak_shaving_into_grid_under_50":
                x = 0
                target_matrix_new = target_matrix[0, :]
                key_performance_indicators_new = key_performance_indicators[0, :]
                while x < target_matrix.shape[0] - 1:
                    x = x + 1

                    if x == 1:
                        target_matrix_new = np.row_stack((target_matrix_new, target_matrix[x, :]))
                        key_performance_indicators_new = np.row_stack((key_performance_indicators_new, key_performance_indicators[x, :]))
                        continue
                    if float(key_performance_indicators[x,7])/1000>100   and target_matrix[x,14] != "peak_shaving_from_grid" and float(target_matrix[x,15]) <0.5 and ((key_performance_indicators[x,2:6].astype(float)>-20000).any() == True):
                        target_matrix_new = np.row_stack((target_matrix_new, target_matrix[x, :]))
                        key_performance_indicators_new = np.row_stack((key_performance_indicators_new, key_performance_indicators[x, :]))
                        continue
            elif y == "plot_strategy_over_100MWh_and_peak_shaving_into_grid_under_10":
                x = 0
                target_matrix_new = target_matrix[0, :]
                key_performance_indicators_new = key_performance_indicators[0, :]
                while x < target_matrix.shape[0] - 1:
                    x = x + 1

                    if x == 1:
                        target_matrix_new = np.row_stack((target_matrix_new, target_matrix[x, :]))
                        key_performance_indicators_new = np.row_stack((key_performance_indicators_new, key_performance_indicators[x, :]))
                        continue
                    if float(key_performance_indicators[x,7])/1000>100   and target_matrix[x,14] != "peak_shaving_from_grid" and float(target_matrix[x,15]) <0.1 and ((key_performance_indicators[x,2:6].astype(float)>-50000).any() == True):
                        target_matrix_new = np.row_stack((target_matrix_new, target_matrix[x, :]))
                        key_performance_indicators_new = np.row_stack((key_performance_indicators_new, key_performance_indicators[x, :]))
                        continue

            elif y == "plot_strategy_over_1000MWh_and_peak_shaving_from_grid_under_10":
                x = 0
                target_matrix_new = target_matrix[0, :]
                key_performance_indicators_new = key_performance_indicators[0, :]
                while x < target_matrix.shape[0] - 1:
                    x = x + 1

                    if x == 1:
                        target_matrix_new = np.row_stack((target_matrix_new, target_matrix[x, :]))
                        key_performance_indicators_new = np.row_stack((key_performance_indicators_new, key_performance_indicators[x, :]))
                        continue
                    if float(key_performance_indicators[x,7])/1000>1000   and target_matrix[x,14] != "peak_shaving_from_grid" and float(target_matrix[x,15]) <0.1 and ((key_performance_indicators[x,2:6].astype(float)>-500000).any() == True):
                        target_matrix_new = np.row_stack((target_matrix_new, target_matrix[x, :]))
                        key_performance_indicators_new = np.row_stack((key_performance_indicators_new, key_performance_indicators[x, :]))
                        continue

            elif y == "plot_strategy_under_100MWh_and_peak_shaving_from_grid_under_10":
                x = 0
                target_matrix_new = target_matrix[0, :]
                key_performance_indicators_new = key_performance_indicators[0, :]
                while x < target_matrix.shape[0] - 1:
                    x = x + 1

                    if x == 1:
                        target_matrix_new = np.row_stack((target_matrix_new, target_matrix[x, :]))
                        key_performance_indicators_new = np.row_stack((key_performance_indicators_new, key_performance_indicators[x, :]))
                        continue
                    if float(key_performance_indicators[x,7])/1000<100   and target_matrix[x,14] != "peak_shaving_from_grid" and float(target_matrix[x,15]) <0.1 and ((key_performance_indicators[x,2:6].astype(float)>-500000).any() == True):
                        target_matrix_new = np.row_stack((target_matrix_new, target_matrix[x, :]))
                        key_performance_indicators_new = np.row_stack((key_performance_indicators_new, key_performance_indicators[x, :]))
                        continue


            elif y=="plot_strategy_peak_shave_from_grid":

                B =(target_matrix[np.any(target_matrix == "Weather", axis=1)])
                A = (target_matrix[np.any(target_matrix == "peak_shaving_from_grid", axis=1)])
                target_matrix_new=np.append(B,A,axis=0)
                key_performance_indicators_new=key_performance_indicators.copy()
                i=0
                while i < (len(target_matrix[:,14])-1):
                    i=i+1
                    if target_matrix[i,14] != "peak_shaving_from_grid":
                        key_performance_indicators_new[i,0] = "delete"

            key_performance_indicators_new = np.delete(key_performance_indicators_new, np.where(key_performance_indicators_new == "delete")[0], 0)
        else:
            breaker= True
            return 0, 0, breaker
        #elif self.flags["plot_strategy_peak_shave_into_grid"]:
            #pass
        return target_matrix_new , key_performance_indicators_new, breaker


    def calculate_correlations(self,target_matrix,key_performance_indicators):
        for house in self.flags_houses:
            target_matrix_new_after_house, key_performance_indicators_new_after_house, breaker = self.sort_out_because_of_house_choosing(
                target_matrix=target_matrix, key_performance_indicators=key_performance_indicators, x=house)
            if breaker:
                continue

    def plot_heat_map(self,target_matrix,key_performance_indicators):

        for kpi in key_performance_indicators[0,:]:
            if kpi== "OwnConsumption" and self.flags_kpis.get("plot_own_consumption")==True:
                pass
            elif kpi == "Autarky" and self.flags_kpis.get("plot_autarky") == True:
                pass
            elif kpi == "NetPresentValue" and self.flags_kpis.get("plot_net_present_value") == True:
                pass
            elif kpi == "DeltaNetPresentValue" and self.flags_kpis.get("plot_net_present_value") == True:
                pass
            elif kpi == "DeltaNetPresentValueHigh" and self.flags_kpis.get("plot_net_present_value") == True:
                pass
            elif kpi == "DeltaNetPresentValueHigh&high_Elect_price" and self.flags_kpis.get("plot_net_present_value") == True:
                pass
            else:

                continue
            for house in self.flags_houses:
                if self.flags_houses[house]==False:
                    continue
                target_matrix_new_after_house, key_performance_indicators_new_after_house, breaker=self.sort_out_because_of_house_choosing(target_matrix=target_matrix,key_performance_indicators=key_performance_indicators, x=house)
                if breaker:
                    continue
                for strategy in self.flags_strategy:
                    if self.flags_strategy[strategy] == False:
                        continue
                    target_matrix_after_stragey, key_performance_indicators_new_after_strategy, breaker= self.sort_out_because_of_strategy_choosing(target_matrix=target_matrix_new_after_house, key_performance_indicators=key_performance_indicators_new_after_house,y=strategy )
                    if breaker:
                        continue
                    for component in self.flags_components:
                        if self.flags_components[component] == False:
                            continue
                        Z, x ,y, breaker=self.transform_data_for_plot(target_matrix=target_matrix_after_stragey, key_performance_indicators=key_performance_indicators_new_after_strategy,kpi=kpi,component=component)
                        if breaker == True and Z==0:
                            print(""+house+" with "+strategy+" has no simulation results and can't be printed")
                            continue
                        elif breaker == True and Z==1:
                            continue

                        fig, ax = plt.subplots()
                        labelsize=11


                        mpl.rcParams.update({'font.size': labelsize})
                        from matplotlib import colors
                        if kpi == "OwnConsumption" or kpi== "Autarky":
                            divnorm = colors.TwoSlopeNorm(vmin=0, vcenter=0.5, vmax=1)
                        else:
                            divnorm = colors.TwoSlopeNorm( vmin=-5000000, vcenter=0, vmax=6000000)
                        cmap = ListedColormap(["darkred", "firebrick", "indianred", "lightcoral","coral", "lightsalmon","lightgreen","greenyellow","yellowgreen","limegreen","forestgreen","darkgreen"])
                        if component == "plot_net_present_value":


                            import matplotlib.colors as mcolors

                            data = np.random.rand(10, 10) * 2 - 1

                            # sample the colormaps that you want to use. Use 128 from each so we get 256
                            # colors in total
                            colors2 = plt.cm.Greens(np.linspace(0.3, 1, 128))
                            colors1 = plt.cm.OrRd_r(np.linspace(0, 0.6, 128))

                            # combine them and build a new colormap
                            colors = np.vstack((colors1, colors2))
                            mymap = mcolors.LinearSegmentedColormap.from_list('my_colormap', colors)
                            cmap = cm.get_cmap(mymap, 11)

                            cax=ax.pcolormesh(Z,cmap=cmap,norm=divnorm ) # vmax=1 for own consumption good


                        else:
                            continue
                            cax=ax.pcolormesh(Z,cmap=cmap,norm=divnorm)   #vmax=1 for own consumption good
                        cbar = fig.colorbar(cax,orientation="horizontal")
                        cbar.ax.set_ylabel(kpi)
                        #Always set up to 8 ticks
                        number_of_ticks=4
                        ticker=np.round(len(x)/number_of_ticks)

                        tick_range_x=(max(x)-min(x))/number_of_ticks
                        tick_range_y=(max(np.round(y, 1))-min(np.round(y,1)))/number_of_ticks
                        x_min=min(np.round(x,1))
                        x_max = max(np.round(x, 1))
                        y_min=min(np.round(y,1))
                        y_max = max(np.round(y, 1))



                        ax.set_xticks(range(len(x)+1))
                        ax.set_yticks(range(len(y)+1))
                        #cax.set_bad(color='grey')
                        x=np.append(x,x[len(x) - 1]+x[1]-x[0])
                        y=np.append(y,y[len(y) - 1]+y[1]-y[0])
                        list_xticklabels = list(np.round(x, 1))
                        list_yticklabels = list(np.round(y, 1))
                        counter=0
                        listx=[]
                        while counter<len(list_xticklabels):
                            if counter%ticker!=0:
                                list_xticklabels[counter]=None
                                list_yticklabels[counter] = None
                            else:
                                listx=np.append(listx,int(counter))
                            counter=counter+1

                        ax.set_xticklabels(list_xticklabels)
                        ax.set_yticklabels(list_yticklabels)
                        ax.set_xticks(listx)
                        ax.set_yticks(listx)
                        ax.set_title("industry")
                        #ax.set_xticklabels(xticklabels)


                        if component == "plot_h2_storage_relative_demand":
                            plt.xlabel('PV-Power kWp/Battery-Capacity kWh')
                            plt.ylabel('H2 Storage in litres / MWh')
                        elif component == "plot_h2_storage_relative_battery":
                            plt.xlabel('PV-Power kWp/Demand MWh')
                            plt.ylabel('H2 Storage in litres / BatteryCapacity kWh')
                        elif component == "plot_net_present_value":
                            #plt.xlabel('PV-Power kWp/MWh')
                            plt.ylabel('1e6=1Million€')
                        else:
                            #plt.xlabel('PV-Power kWp/MWh')
                            plt.ylabel('Battery-Capacity kWh/MWh')

                    #hier ne ebsser Abrufung bauen!!!!
                        labelsize=11

                        mpl.rcParams.update({'font.size': labelsize})


                        plt.tight_layout()
                        fig.set_size_inches(3.5, 3.5)
                        plt.tight_layout()
                        plt.savefig(""+str(kpi)+"" + component + "_" + house + " _with_" + strategy + ".png")
                        #plt.show()


                    '''
                    fig, ax = plt.subplots()
                    sns.set_theme()
                    uniform_data = Z
                    sns.heatmap(uniform_data,vmin=0, vmax=1, cbar_kws={'label': kpi}, cmap="YlGnBu")
                    ax.set(xlabel='PV-Power kWp/MWh', ylabel='Battery-Capacity kWp/MWh')
                    ax.set_title(""+house+" with " +strategy+"")
                    ax.set_xlim(min(x),max(x))
                    ax.set_xticks(range(0,int(max(x))))

                    ax.set_ylim(min(y), max(y))
                    ax.set_yticks(range(0,int(max(y))))

                    ax.invert_yaxis()

                    plt.show()
                    '''





    def run(self):
        #I am working with numpy array instead of dict, bec. can be made better to grafics.

        #Names are not consistent in Components, so hard to automize
        target_matrix= np.array(["Weather",
                                 "HouseType",
                                 "WarmWaterDemand",
                                 "HeatingWaterDemand",
                                 "ElectricityDemand",
                                 "PVSystemPower",
                                 "BatteryCapacity",
                                 "HeatPumpPower",
                                 "GasHeaterPower",
                                 "CHPPower",
                                 "ElectrolyzerPower",
                                 "HeatStorageVolume",
                                 "WarmWaterStorageVolume",
                                 "HydrogenStorageVolume",
                                 "ControlStrategy",
                                 "PercentageToShave",
                                 "LimitToShave",
                                 "SimulationNumber"])

        key_performance_indicators=np.array(["OwnConsumption",
                                             "Autarky",
                                             "FullCycles",
                                             "DeltaNetPresentValue",
                                             "DeltaNetPresentValueLow",
                                             "DeltaNetPresentValueHigh",
                                             "ReturnOnInvestment",
                                             "ReturnOnInvestmentLow",
                                             "ReturnOnInvestmentHigh",
                                             "PayBackDuration",
                                             "PayBackDurationLow",
                                             "PayBackDurationHigh",
                                             "UtilisationHoursWithBattery",
                                             "DeltaUtilisationHours",
                                             "AnnaulDemand"
                                             ])



        #"NetPresentValue_high_Elect_price",
        #"NetPresentValue_low_Batteryprice",
        #"NetPresentValue_low_Batteryprice&high_Elect_price"


        new_list = self.get_all_relevant_folders()
        #target_matrix=self.get_json_data(new_list,target_matrix)

        #key_performance_indicators=self.get_pickle_informations(new_list,key_performance_indicators,target_matrix)

        #sort out for salib and clean if same Simulations
        #check if all simulation results are avaiable



        target_matrix=np.load("target_matrix_sorted_industry_OC.npy",allow_pickle=True )
        key_performance_indicators=np.load("kpis_sorted_industry_OC.npy",allow_pickle=True )
        self.plot_heat_map(target_matrix,key_performance_indicators)


my_Post_Processor=PostProcessor(folder_name="basic_household_implicit_salib_household",
                                json_file_name="cfg",
                                pickle_file_name="data",
                                start_date="20220123_133200",
                                end_date="20220123_231200",
                                heat_map_precision_factor=23,
                                simulation_number_to_be_analyzed=50000# can bes as well None, than it checks for all simulations in between start and end date
                                )
my_Post_Processor.run()
#f=open("HiSim/hisim/results/basic_household_implicit_hyper_cube_20211113_130857/cfg.json",)
#data = json.load(f)
'''
Metalworking 14
development
Water treatment
Producing industry
Manufacturing industry 3
Hotel
Health care services
Services 2
Chemical industry
Waste disposal 4
Woodworking industry 2
Building materials 1
Woodworking industry 3
Furniture retail 3
Gravel 4
Production 2
Quarry 4
Polymer processing 2
Sawmill 1
Garden 2
School 35
(Pre-)School 1
Other 8
Zoo
Event hall 4
Graveyard 2
Office building 15
Water pump 5
Swimming Pool 4
Gym 2
Library 1
Tunnel 1
Firefighters 1
Trailer park
Garage
toolmanufactor # aber nicht so als Name
electroplating # aber nicht so als anmae
'''