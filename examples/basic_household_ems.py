from typing import Optional
from hisim.simulator import SimulationParameters
from hisim.components import loadprofilegenerator_connector
from hisim.components import weather
from hisim.components import building
from hisim.components import controller_l2_energy_management_system
from hisim.components import generic_hot_water_storage
from hisim.components import generic_gas_heater

from hisim import utils
from hisim import loadtypes as lt
import os
import numpy as np
import pandas as pd

__authors__ = "Maximilian Hillen"
__copyright__ = "Copyright 2021, the House Infrastructure Project"
__credits__ = ["Noah Pflugradt"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Maximilian Hillen"
__email__ = "maximilian.hillen@rwth-aachen.de"
__status__ = "development"


def basic_household_only_heat(my_sim, my_simulation_parameters: Optional[SimulationParameters] = None):
    """
    This setup function emulates an household including
    the basic components. Here the residents have their
    heating needs covered by a gas heater and a heating
    water storage. The controller_l2_ems controls according
    to the storage tempreature the gas heater.

    - Simulation Parameters
    - Components
        - Occupancy (Residents' Demands)
        - Weather
        - GasHeater
        - HeatingStorage
        - Controller2EMS
    """

    ##### System Parameters #####

    # Set simulation parameters
    year = 2021
    seconds_per_timestep = 60*15

    # Set weather
    location = "Aachen"

    # Set occupancy
    occupancy_profile = "CH01"

    # Controller
    initial_temperature=22
    temperature_storage_target_heating_water=35

    # Building
    minimal_building_temperature=20

    # Heat Storage
    #initial_temperature=22
    #initial_temperature_heating_storage = temperature_storage_target_heating_water

    ##### Build Components #####

    # Build system parameters
    if my_simulation_parameters is None:
        my_simulation_parameters = SimulationParameters.full_year_all_options(year=year,
                                                                                 seconds_per_timestep=seconds_per_timestep)
    my_sim.set_simulation_parameters (my_simulation_parameters)

    # Build occupancy
    my_occupancy = loadprofilegenerator_connector.Occupancy(config=loadprofilegenerator_connector.Occupancy.get_default_config(), my_simulation_parameters=my_simulation_parameters)

    # Build Weather
    my_weather = weather.Weather(config=weather.Weather.get_default_config(), my_simulation_parameters= my_simulation_parameters)

    # Build Gas Heater
    my_gas_heater = generic_gas_heater.GasHeater(config=generic_gas_heater.GasHeater.get_default_config(),my_simulation_parameters=my_simulation_parameters)

    # Build Building
    my_building = building.Building(config=building.Building.get_default_config(),my_simulation_parameters= my_simulation_parameters)
    my_building_controller = building.BuildingController( config=building.BuildingController.get_default_config(),
                                                          my_simulation_parameters= my_simulation_parameters)

    # Build Storage
    my_storage = generic_hot_water_storage.HeatStorage(config=generic_hot_water_storage.HeatStorage.get_default_config(),
                                                       my_simulation_parameters=my_simulation_parameters)

    my_storage_controller = generic_hot_water_storage.HeatStorageController(config=generic_hot_water_storage.HeatStorageController.get_default_config(),
                                                                            my_simulation_parameters=my_simulation_parameters)

    # Build Controller
    my_controller_heat= controller_l2_energy_management_system.ControllerHeat(config= controller_l2_energy_management_system.ControllerHeat.get_default_config(),
                                                                               my_simulation_parameters= my_simulation_parameters)

    my_building.connect_only_predefined_connections( my_weather, my_occupancy )


    my_storage.connect_input(my_storage.ThermalDemandHeatingWater,
                              my_storage_controller.ComponentName,
                              my_storage_controller.RealThermalDemandHeatingWater)
    my_storage.connect_input(my_storage.ControlSignalChooseStorage,
                              my_controller_heat.ComponentName,
                              my_controller_heat.ControlSignalChooseStorage)

    my_storage_controller.connect_input(my_storage_controller.TemperatureHeatingStorage,
                              my_storage.ComponentName,
                              my_storage.WaterOutputTemperatureHeatingWater)
    my_storage_controller.connect_input(my_storage_controller.BuildingTemperature,
                              my_building.ComponentName,
                              my_building.TemperatureMean)
    my_storage_controller.connect_input(my_storage_controller.ReferenceMaxHeatBuildingDemand,
                              my_building.ComponentName,
                              my_building.ReferenceMaxHeatBuildingDemand)
    my_storage_controller.connect_input(my_storage_controller.RealHeatBuildingDemand,
                              my_building_controller.ComponentName,
                              my_building_controller.RealHeatBuildingDemand)

    my_building_controller.connect_input(my_building_controller.ReferenceMaxHeatBuildingDemand,
                              my_building.ComponentName,
                              my_building.ReferenceMaxHeatBuildingDemand)
    my_building_controller.connect_input(my_building_controller.ResidenceTemperature,
                              my_building.ComponentName,
                              my_building.TemperatureMean)
    my_building.connect_input(my_building.ThermalEnergyDelivered,
                              my_storage.ComponentName,
                              my_storage.RealHeatForBuilding)

    my_controller_heat.connect_input(my_controller_heat.StorageTemperatureHeatingWater,
                              my_storage.ComponentName,
                              my_storage.WaterOutputTemperatureHeatingWater)

    my_controller_heat.connect_input(my_controller_heat.ResidenceTemperature,
                              my_building.ComponentName,
                              my_building.TemperatureMean)

    my_gas_heater.connect_input(my_gas_heater.ControlSignal,
                              my_controller_heat.ComponentName,
                              my_controller_heat.ControlSignalGasHeater)
    my_gas_heater.connect_input(my_gas_heater.MassflowInputTemperature,
                              my_storage.ComponentName,
                              my_storage.WaterOutputStorageforHeaters)
    my_storage.connect_input(my_storage.ThermalInputPower1,
                              my_gas_heater.ComponentName,
                              my_gas_heater.ThermalOutputPower)

    my_sim.add_component(my_building_controller)
    my_sim.add_component(my_controller_heat)
    my_sim.add_component(my_storage_controller)

    my_sim.add_component(my_storage)
    my_sim.add_component(my_gas_heater)
    my_sim.add_component(my_building)
    my_sim.add_component(my_weather)
    my_sim.add_component(my_occupancy)
