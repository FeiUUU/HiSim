from hisim import component as cp
#import components as cps
#import components
from hisim.components import generic_hot_water_storage
from hisim import loadtypes as lt
from hisim.simulationparameters import SimulationParameters
from tests import functions_for_testing as fft

def test_storage():

    seconds_per_timestep = 60
    my_simulation_parameters = SimulationParameters.one_day_only(2017,seconds_per_timestep)
    # Storage
    V_SP_heating_water = 1000
    V_SP_warm_water = 200
    temperature_of_warm_water_extratcion = 32
    ambient_temperature = 15

    #===================================================================================================================
    # Set Storage
    my_storage_config= generic_hot_water_storage.HeatStorage.get_default_config()
    my_storage_config.V_SP_heating_water =V_SP_heating_water
    my_storage_config.V_SP_warm_water = V_SP_warm_water
    my_storage_config.temperature_of_warm_water_extratcion = temperature_of_warm_water_extratcion
    my_storage_config.ambient_temperature = ambient_temperature

    my_storage = generic_hot_water_storage.HeatStorage(config=my_storage_config,
                                     my_simulation_parameters=my_simulation_parameters)

    thermal_demand_heating_water = cp.ComponentOutput("FakeThermalDemandHeatingWater",
                             "ThermalDemandHeatingWater",
                                                      lt.LoadTypes.ANY,
                                                      lt.Units.PERCENT)

    thermal_demand_warm_water = cp.ComponentOutput("FakeThermalDemandWarmWater",
                              "ThermalDemandWarmWater",
                                                   lt.LoadTypes.WATER,
                                                   lt.Units.CELSIUS)

    control_signal_choose_storage = cp.ComponentOutput("FakeControlSignalChooseStorage",
                              "ControlSignalChooseStorage",
                                                       lt.LoadTypes.WATER,
                                                       lt.Units.CELSIUS)

    thermal_input_power1 = cp.ComponentOutput("FakeThermalInputPower1",
                              "ThermalInputPower1",
                                              lt.LoadTypes.WATER,
                                              lt.Units.CELSIUS)

    my_storage.thermal_demand_heating_water.SourceOutput = thermal_demand_heating_water
    my_storage.thermal_demand_warm_water.SourceOutput = thermal_demand_warm_water
    my_storage.control_signal_choose_storage.SourceOutput = control_signal_choose_storage
    my_storage.thermal_input_power1.SourceOutput = thermal_input_power1

    number_of_outputs = fft.get_number_of_outputs([thermal_demand_heating_water,
                                        thermal_demand_warm_water,
                                        control_signal_choose_storage,
                                        thermal_input_power1,
                                        my_storage])
    stsv: cp.SingleTimeStepValues = cp.SingleTimeStepValues(number_of_outputs)

    # Add Global Index and set values for fake Inputs
    fft.add_global_index_of_components([thermal_demand_heating_water,
                                        thermal_demand_warm_water,
                                        control_signal_choose_storage,
                                        thermal_input_power1,
                                        my_storage])

    stsv.values[thermal_demand_heating_water.GlobalIndex] = 2000
    stsv.values[thermal_demand_warm_water.GlobalIndex] = 400
    stsv.values[control_signal_choose_storage.GlobalIndex] = 1
    stsv.values[thermal_input_power1.GlobalIndex] = 800

    timestep = 300
    # Simulate

    my_storage.i_restore_state()
    my_storage.i_simulate(timestep, stsv, False)
    # WW-Storage is choosed to be heated up
    assert 1 == stsv.values[control_signal_choose_storage.GlobalIndex]
    # Temperature of Heating-Water Storage sinks
    assert 39.97334630595229== stsv.values[my_storage.T_sp_C_hw.GlobalIndex]
    # Temperature of Heating-Water Storage raise
    assert 40.02265485276707 == stsv.values[my_storage.T_sp_C_ww.GlobalIndex]
    # Energy Loss of Storage
    assert 6.26 == stsv.values[my_storage.UA_SP_C.GlobalIndex]
    # Temperature of choosed storage (warm-Water) to be heated up
    assert stsv.values[my_storage.T_sp_C_ww.GlobalIndex] == stsv.values[my_storage.T_sp_C.GlobalIndex]

