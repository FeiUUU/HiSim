import os
import sys
import globals
import numpy as np
import simulator as sim
import loadtypes
import start_simulation
import components as cps
from components import occupancy
from components import weather
from components import building
from components import heat_pump_hplib
from components import controller
from components import storage
from components import pvs
from components import advanced_battery
from components import configuration
import globals
from components.csvloader import CSVLoaderEL


__authors__ = "Max Hillen, Tjarko Tjaden"
__copyright__ = "Copyright 2021, the House Infrastructure Project"
__credits__ = ["Noah Pflugradt"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Max Hillen"
__email__ = "max.hillen@fz-juelich.de"
__status__ = "development"
#power=E3 10E3 25E3 100E3
power = 10E3
#capacitiy=  25 100
capacitiy=100

def basic_household(my_sim,capacity=capacitiy,power=power):
    """
    This setup function represents an household including
    electric and thermal consumption and a heatpump.

    - Simulation Parameters
    - Components
        - Weather
        - Building
        - Occupancy (Residents' Demands)
        - Heat Pump
    """

    ##### System Parameters #####

    # Set simulation parameters
    year = 2021
    seconds_per_timestep = 60*15

    # Set weather
    location = "Aachen"

    # Set occupancy
    occupancy_profile = "CH01"

    # Set building
    building_code = "DE.N.SFH.05.Gen.ReEx.001.002"
    building_class = "medium"
    initial_temperature = 23

    # Set photovoltaic system
    time = 2019

    load_module_data = False
    module_name = "Hanwha_HSL60P6_PA_4_250T__2013_"
    integrateInverter = True
    inverter_name = "ABB__MICRO_0_25_I_OUTD_US_208_208V__CEC_2014_"
    # Set Battery

    # Set heat pump
    hp_manufacturer = "Generic"
    hp_type = 1 # air/water | regulated
    hp_thermal_power = 12000 # W
    hp_t_input = -7 # °C
    hp_t_output = 52 # °C

    # Set warm water storage
    wws_volume = 500 # l
    wws_temp_outlet=35
    wws_temp_ambient=15

    ##### Build Components #####

    # Build system parameters
    my_sim_params: sim.SimulationParameters = sim.SimulationParameters.full_year(year=year,
                                                                                 seconds_per_timestep=seconds_per_timestep)
    my_sim.set_parameters(my_sim_params)

    #ElectricityDemand
    csv_load_power_demand = CSVLoaderEL(component_name="csv_load_power",
                                      csv_filename="loadprofiles/vdi-4655/vdi-4655_sfh-existing_try-1_15min.csv",
                                      column=1,
                                      loadtype=loadtypes.LoadTypes.Electricity,
                                      unit=loadtypes.Units.Watt,
                                      column_name="power_demand",
                                      simulation_parameters=my_sim_params,
                                      multiplier=6)
    my_sim.add_component(csv_load_power_demand)

    # Build occupancy
    #my_occupancy = occupancy.Occupancy(profile=occupancy_profile)
    #my_sim.add_component(my_occupancy)

    # Build Weather
    my_weather = weather.Weather(location=location)
    my_sim.add_component(my_weather)

    # Build building
    '''
    my_building = building.Building(building_code=building_code,
                                        bClass=building_class,
                                        initial_temperature=initial_temperature,
                                        sim_params=my_sim_params,
                                        seconds_per_timestep=seconds_per_timestep)
    '''
    #Build Battery
    fparameter = np.load(globals.HISIMPATH["bat_parameter"])
    my_battery = advanced_battery.AdvancedBattery(my_simulation_parameters=my_sim_params,capacity=capacity)



    #Build Controller
    my_controller = controller.Controller(strategy= "peak_shaving_from_grid",limit_to_shave=500)
    '''
        residual_power = CSVLoader(component_name="residual_power",
                               csv_filename="advanced_battery/Pr_ideal_1min.csv",
                               column=0,
                               loadtype=loadtypes.LoadTypes.Electricity,
                               unit=loadtypes.Units.Watt,
                               column_name="Pr_ideal_1min",
                               simulation_parameters=sim_param)

        sim.add_component(residual_power)
    '''

    '''
    my_building.connect_input(my_building.Altitude,
                              my_weather.ComponentName,
                              my_building.Altitude)
    my_building.connect_input(my_building.Azimuth,
                              my_weather.ComponentName,
                              my_building.Azimuth)
    my_building.connect_input(my_building.DirectNormalIrradiance,
                              my_weather.ComponentName,
                              my_building.DirectNormalIrradiance)
    my_building.connect_input(my_building.DiffuseHorizontalIrradiance,
                              my_weather.ComponentName,
                              my_building.DiffuseHorizontalIrradiance)
    my_building.connect_input(my_building.GlobalHorizontalIrradiance,
                              my_weather.ComponentName,
                              my_building.GlobalHorizontalIrradiance)
    my_building.connect_input(my_building.DirectNormalIrradianceExtra,
                              my_weather.ComponentName,
                              my_building.DirectNormalIrradianceExtra)
    my_building.connect_input(my_building.ApparentZenith,
                             my_weather.ComponentName,
                             my_building.ApparentZenith)
    my_building.connect_input(my_building.TemperatureOutside,
                              my_weather.ComponentName,
                              my_weather.TemperatureOutside)
    my_building.connect_input(my_building.HeatingByResidents,
                              my_occupancy.ComponentName,
                              my_occupancy.HeatingByResidents)
    my_sim.add_component(my_building)
    '''
    '''
    # Build heat pump 
    my_heat_pump = heat_pump_hplib.HeatPumpHplib(model=hp_manufacturer, 
                                                    group_id=hp_type,
                                                    t_in=hp_t_input,
                                                    t_out=hp_t_output,
                                                    p_th_set=hp_thermal_power)
    my_heat_storage = storage.HeatStorage(V_SP = wws_volume,
                                          temperature_of_warm_water_extratcion = wws_temp_outlet,
                                          ambient_temperature=wws_temp_ambient)
                                          
    my_heat_pump.connect_input(my_heat_pump.OnOffSwitch,
                               my_controller.ComponentName,
                               my_controller.ControlSignalHeatPump)
    my_heat_pump.connect_input(my_heat_pump.TemperatureInputPrimary,
                               my_weather.ComponentName,
                               my_weather.TemperatureOutside)
    my_heat_pump.connect_input(my_heat_pump.TemperatureInputSecondary,
                               my_heat_storage.ComponentName,eir
                               my_heat_storage.WaterOutputTemperature)
    my_heat_pump.connect_input(my_heat_pump.TemperatureInputPrimary,
                               my_weather.ComponentName,
                               my_weather.TemperatureOutside)
    my_heat_pump.connect_input(my_heat_pump.TemperatureAmbient,
                               my_weather.ComponentName,
                               my_weather.TemperatureOutside)
    my_sim.add_component(my_heat_pump)


    # Build heat storage

    my_heat_storage.connect_input(my_heat_storage.InputMass1,
                               my_heat_pump.ComponentName,
                               my_heat_pump.MassFlowOutput)
    my_heat_storage.connect_input(my_heat_storage.InputTemp1,
                               my_heat_pump.ComponentName,
                               my_heat_pump.TemperatureOutput)
    my_heat_storage.connect_input(my_heat_storage.InputTemp1,
                               my_heat_pump.ComponentName,
                               my_heat_pump.TemperatureOutput)

    my_sim.add_component(my_heat_storage)
    '''
    my_photovoltaic_system = pvs.PVSystem(time=time,
                                          location=location,
                                          power=power,
                                          load_module_data=load_module_data,
                                          module_name=module_name,
                                          integrateInverter=integrateInverter,
                                          inverter_name=inverter_name,
                                          my_simulation_parameters=my_sim_params)
    my_photovoltaic_system.connect_input(my_photovoltaic_system.TemperatureOutside,
                                         my_weather.ComponentName,
                                         my_weather.TemperatureOutside)
    my_photovoltaic_system.connect_input(my_photovoltaic_system.DirectNormalIrradiance,
                                         my_weather.ComponentName,
                                         my_weather.DirectNormalIrradiance)
    my_photovoltaic_system.connect_input(my_photovoltaic_system.DirectNormalIrradianceExtra,
                                         my_weather.ComponentName,
                                         my_weather.DirectNormalIrradianceExtra)
    my_photovoltaic_system.connect_input(my_photovoltaic_system.DiffuseHorizontalIrradiance,
                                         my_weather.ComponentName,
                                         my_weather.DiffuseHorizontalIrradiance)
    my_photovoltaic_system.connect_input(my_photovoltaic_system.GlobalHorizontalIrradiance,
                                         my_weather.ComponentName,
                                         my_weather.GlobalHorizontalIrradiance)
    my_photovoltaic_system.connect_input(my_photovoltaic_system.Azimuth,
                                         my_weather.ComponentName,
                                         my_weather.Azimuth)
    my_photovoltaic_system.connect_input(my_photovoltaic_system.ApparentZenith,
                                         my_weather.ComponentName,
                                         my_weather.ApparentZenith)
    my_photovoltaic_system.connect_input(my_photovoltaic_system.WindSpeed,
                                         my_weather.ComponentName,
                                         my_weather.WindSpeed)

    my_battery.connect_input(my_battery.LoadingPowerInput,
                               my_controller.ComponentName,
                               my_controller.ElectricityToOrFromBatteryTarget)

    my_controller.connect_input(my_controller.ElectricityToOrFromBatteryReal,
                               my_battery.ComponentName,
                               my_battery.ACBatteryPower)


    my_controller.connect_input(my_controller.ElectricityConsumptionBuilding,
                               csv_load_power_demand.ComponentName,
                               csv_load_power_demand.Output1)
    my_controller.connect_input(my_controller.ElectricityOutputPvs,
                               my_photovoltaic_system.ComponentName,
                               my_photovoltaic_system.ElectricityOutput)

    my_sim.add_component(my_photovoltaic_system)
    my_sim.add_component(my_battery)
    my_sim.add_component(my_controller)



def basic_household_implicit(my_sim):
    pass

