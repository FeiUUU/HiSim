from typing import Optional, List, Union
import hisim.components.random_numbers
from hisim.simulator import SimulationParameters
from hisim.components import loadprofilegenerator_connector
from hisim.components import advanced_battery_bslib
from hisim.components import weather
from hisim.components import generic_gas_heater
from hisim.components import controller_l2_energy_management_system as cl2
from hisim.components import generic_pv_system
from hisim.components import building
from hisim.components import advanced_fuel_cell
from hisim.components.random_numbers import RandomNumbers
from hisim.components.example_transformer import Transformer
from hisim import loadtypes as lt
from hisim import component as cp
import numpy as np
import os
from hisim import utils


def basic_household_explicit(my_sim, my_simulation_parameters: Optional[SimulationParameters] = None):
    """
    In this example a generic controller is added. The generic controller
    makes it possible to add component generically.
    Here two fuel_cell/chp_systems and two batteries
    are added.
    """
    year = 2018
    seconds_per_timestep = 60 * 15
    # Set weather
    location = "Aachen"
    # Set occupancy
    occupancy_profile = "CH01"

    # Set photovoltaic system
    time = 2019
    power = 3E3
    load_module_data = False
    module_name = "Hanwha_HSL60P6_PA_4_250T__2013_"
    integrateInverter = True
    inverter_name = "ABB__MICRO_0_25_I_OUTD_US_208_208V__CEC_2014_"
    name = 'PVSystem'
    azimuth  = 180
    tilt  = 30
    source_weight  = 0

    if my_simulation_parameters is None:
        my_simulation_parameters = SimulationParameters.full_year_all_options(year=year,
                                                                                 seconds_per_timestep=seconds_per_timestep)
       # my_simulation_parameters = SimulationParameters.january_only(year=year, seconds_per_timestep=seconds_per_timestep)
       # my_simulation_parameters.enable_all_options( )                                                                          
       
    my_sim.set_simulation_parameters(my_simulation_parameters)

    my_advanced_battery_config_1 = advanced_battery_bslib.BatteryConfig( system_id='SG1',
                                                                         p_inv_custom=5.0,
                                                                         e_bat_custom=10.0,
                                                                         name="Battery",
                                                                         source_weight = 1 )
    my_advanced_battery_config_2 = advanced_battery_bslib.BatteryConfig( system_id='SG1',
                                                                         p_inv_custom=2.5,
                                                                         e_bat_custom=5.0,
                                                                         name="Battery",
                                                                         source_weight = 2 )
    my_advanced_battery_1 = advanced_battery_bslib.Battery(my_simulation_parameters=my_simulation_parameters,
                                                           config= my_advanced_battery_config_1)
    my_advanced_battery_2 = advanced_battery_bslib.Battery(my_simulation_parameters=my_simulation_parameters,
                                                           config= my_advanced_battery_config_2)

    my_advanced_fuel_cell_config_1 = advanced_fuel_cell.CHP.get_default_config()
    my_advanced_fuel_cell_config_2 = advanced_fuel_cell.CHP.get_default_config()
    my_advanced_fuel_cell_config_1.name="CHP1"
    my_advanced_fuel_cell_config_2.name= "CHP2"

    my_advanced_fuel_cell_1 = advanced_fuel_cell.CHP(my_simulation_parameters=my_simulation_parameters,
                                                      config=my_advanced_fuel_cell_config_1)
    my_advanced_fuel_cell_2 = advanced_fuel_cell.CHP(my_simulation_parameters=my_simulation_parameters,
                                                      config=my_advanced_fuel_cell_config_2)
    my_cl2 = cl2.ControllerElectricityGeneric(my_simulation_parameters=my_simulation_parameters)

    my_occupancy_config = loadprofilegenerator_connector.OccupancyConfig(profile_name="CH01")
    my_occupancy = loadprofilegenerator_connector.Occupancy( config=my_occupancy_config, my_simulation_parameters = my_simulation_parameters )

    my_weather_config = weather.WeatherConfig(location=location)
    my_weather = weather.Weather( config=my_weather_config, my_simulation_parameters = my_simulation_parameters,
                                  my_simulation_repository = my_sim.simulation_repository )

    my_photovoltaic_system_config= generic_pv_system.PVSystemConfig(time=time,
                                          location=location,
                                          power=power,
                                          load_module_data=load_module_data,
                                          module_name=module_name,
                                          integrate_inverter=integrateInverter,
                                          tilt=tilt,
                                          azimuth = azimuth,
                                          inverter_name=inverter_name,
                                          source_weight = source_weight,
                                          name=name)
    my_photovoltaic_system = generic_pv_system.PVSystem(my_simulation_parameters=my_simulation_parameters,
                                                        my_simulation_repository=my_sim.simulation_repository,
                                                        config=my_photovoltaic_system_config)
    my_photovoltaic_system.connect_only_predefined_connections(my_weather)

    my_cl2.add_component_inputs_and_connect(source_component_classes = [ my_occupancy ],
                                            outputstring = 'ElectricityOutput',
                                            source_load_type = lt.LoadTypes.ELECTRICITY,
                                            source_unit = lt.Units.WATT,
                                            source_tags = [lt.InandOutputType.CONSUMPTION],
                                            source_weight = 999)
    my_cl2.add_component_inputs_and_connect(source_component_classes = [ my_photovoltaic_system ],
                                            outputstring = 'ElectricityOutput',
                                            source_load_type = lt.LoadTypes.ELECTRICITY,
                                            source_unit = lt.Units.WATT,
                                            source_tags = [lt.InandOutputType.PRODUCTION],
                                            source_weight = 999)
    my_cl2.add_component_input_and_connect(source_component_class = my_advanced_battery_1,
                                           source_component_output = my_advanced_battery_1.AcBatteryPower,
                                           source_load_type = lt.LoadTypes.ELECTRICITY,
                                           source_unit = lt.Units.WATT,
                                           source_tags = [lt.ComponentType.BATTERY, lt.InandOutputType.ELECTRICITY_REAL],
                                           source_weight = 1)
    my_cl2.add_component_input_and_connect(source_component_class = my_advanced_battery_2,
                                           source_component_output = my_advanced_battery_2.AcBatteryPower,
                                           source_load_type = lt.LoadTypes.ELECTRICITY,
                                           source_unit = lt.Units.WATT,
                                           source_tags = [lt.ComponentType.BATTERY, lt.InandOutputType.ELECTRICITY_REAL],
                                           source_weight = 2)

    electricity_to_or_from_battery_target_1 = my_cl2.add_component_output(source_output_name = lt.InandOutputType.ELECTRICITY_TARGET,
                                                                          source_tags = [lt.ComponentType.BATTERY, lt.InandOutputType.ELECTRICITY_TARGET],
                                                                          source_weight = my_advanced_battery_1.source_weight,
                                                                          source_load_type = lt.LoadTypes.ELECTRICITY,
                                                                          source_unit = lt.Units.WATT)
    electricity_to_or_from_battery_target_2 = my_cl2.add_component_output(source_output_name = lt.InandOutputType.ELECTRICITY_TARGET,
                                                                          source_tags = [lt.ComponentType.BATTERY, lt.InandOutputType.ELECTRICITY_TARGET],
                                                                          source_weight = my_advanced_battery_2.source_weight,
                                                                          source_load_type = lt.LoadTypes.ELECTRICITY,
                                                                          source_unit = lt.Units.WATT)

    my_advanced_battery_1.connect_dynamic_input( input_fieldname = advanced_battery_bslib.Battery.LoadingPowerInput,
                                                 src_object = electricity_to_or_from_battery_target_1 )
    my_advanced_battery_2.connect_dynamic_input( input_fieldname = advanced_battery_bslib.Battery.LoadingPowerInput,
                                                 src_object = electricity_to_or_from_battery_target_2 )
    
    print( type(my_advanced_fuel_cell_1.ElectricityOutput))

    my_cl2.add_component_input_and_connect(source_component_class = my_advanced_fuel_cell_1,
                                           source_component_output = my_advanced_fuel_cell_1.ElectricityOutput,
                                           source_load_type = lt.LoadTypes.ELECTRICITY,
                                           source_unit = lt.Units.WATT,
                                           source_tags = [lt.ComponentType.FUEL_CELL, lt.InandOutputType.ELECTRICITY_REAL],
                                           source_weight = 3)
    my_cl2.add_component_input_and_connect(source_component_class = my_advanced_fuel_cell_2,
                                           source_component_output = my_advanced_fuel_cell_2.ElectricityOutput,
                                           source_load_type = lt.LoadTypes.ELECTRICITY,
                                           source_unit = lt.Units.WATT,
                                           source_tags = [lt.ComponentType.FUEL_CELL, lt.InandOutputType.ELECTRICITY_REAL],
                                           source_weight = 4)

    electricity_from_fuel_cell_target_1 = my_cl2.add_component_output(source_output_name = lt.InandOutputType.ELECTRICITY_TARGET,
                                                                      source_tags = [lt.ComponentType.FUEL_CELL, lt.InandOutputType.ELECTRICITY_TARGET],
                                                                      source_weight = 3,
                                                                      source_load_type = lt.LoadTypes.ELECTRICITY,
                                                                      source_unit = lt.Units.WATT)
    electricity_from_fuel_cell_target_2 = my_cl2.add_component_output(source_output_name=lt.InandOutputType.ELECTRICITY_TARGET,
                                                                      source_tags = [lt.ComponentType.FUEL_CELL, lt.InandOutputType.ELECTRICITY_TARGET],
                                                                      source_weight = 4,
                                                                      source_load_type = lt.LoadTypes.ELECTRICITY,
                                                                      source_unit = lt.Units.WATT)

    my_advanced_fuel_cell_1.connect_dynamic_input( input_fieldname=advanced_fuel_cell.CHP.ElectricityFromCHPTarget,
                                                    src_object=electricity_from_fuel_cell_target_1 )
    my_advanced_fuel_cell_2.connect_dynamic_input( input_fieldname=advanced_fuel_cell.CHP.ElectricityFromCHPTarget,
                                                    src_object=electricity_from_fuel_cell_target_2 )

    my_sim.add_component( my_advanced_battery_1 )
    my_sim.add_component( my_advanced_battery_2 )
    my_sim.add_component( my_advanced_fuel_cell_1 )
    my_sim.add_component( my_advanced_fuel_cell_2 )
    my_sim.add_component( my_cl2)
    my_sim.add_component( my_weather )
    my_sim.add_component( my_occupancy )
    my_sim.add_component( my_photovoltaic_system )

