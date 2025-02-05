# -*- coding: utf-8 -*-
"""
Created on Fri Jul 22 10:06:48 2022

@author: Johanna
"""

# -*- coding: utf-8 -*-
"""
Created on Thu Jul 21 20:04:59 2022

@author: Johanna
"""

from hisim import component as cp
from tests import functions_for_testing as fft
from hisim import loadtypes as lt

from hisim.simulationparameters import SimulationParameters
from hisim.components import generic_CHP

def test_chp_system():

    seconds_per_timestep = 60
    my_simulation_parameters = SimulationParameters.one_day_only( 2017, seconds_per_timestep )
    
    my_chp_config = generic_CHP.GCHP.get_default_config( )
    my_chp = generic_CHP.GCHP( config = my_chp_config,
                              my_simulation_parameters = my_simulation_parameters )
    my_chp_controller_config = generic_CHP.L1_Controller.get_default_config( )
    my_chp_controller = generic_CHP.L1_Controller( config = my_chp_controller_config,
                                                   my_simulation_parameters = my_simulation_parameters )
    
    # Set Fake Inputs
    electricity_target = cp.ComponentOutput( 'FakeElectricityTarget',
                                             "l2_ElectricityTarget",
                                             lt.LoadTypes.ELECTRICITY,
                                             lt.Units.WATT)
    hydrogensoc = cp.ComponentOutput( 'FakeH2SOC',
                                      'HydrogenSOC',
                                      lt.LoadTypes.HYDROGEN,
                                      lt.Units.PERCENT)
    l2_devicesignal = cp.ComponentOutput( 'FakeHeatSignal',
                                          'l2_DeviceSignal',
                                          lt.LoadTypes.ON_OFF,
                                          lt.Units.BINARY)
    
    number_of_outputs = fft.get_number_of_outputs( [ my_chp, my_chp_controller, electricity_target, hydrogensoc, l2_devicesignal ] )
    stsv: cp.SingleTimeStepValues = cp.SingleTimeStepValues( number_of_outputs )

    my_chp_controller.ElectricityTargetC.SourceOutput = electricity_target
    my_chp_controller.HydrogenSOCC.SourceOutput = hydrogensoc
    my_chp_controller.l2_DeviceSignalC.SourceOutput = l2_devicesignal
    my_chp.l1_DeviceSignalC.SourceOutput = my_chp_controller.l1_DeviceSignalC

    # Add Global Index and set values for fake Inputs
    fft.add_global_index_of_components( [ my_chp, my_chp_controller, electricity_target, hydrogensoc, l2_devicesignal ] )

    #test if chp runs when hydrogen in storage and heat as well as electricity needed
    stsv.values[ electricity_target.GlobalIndex ] = 2.5e3
    stsv.values[ hydrogensoc.GlobalIndex ] = 50
    stsv.values[ l2_devicesignal.GlobalIndex ] = 1
    
    for t in range( int( ( my_chp_controller_config.min_idle_time / seconds_per_timestep ) + 2 ) ):
        my_chp_controller.i_simulate( t, stsv,  False )
        my_chp.i_simulate( t, stsv, False )
        
    print( stsv.values[ my_chp.ThermalEnergyDeliveredC.GlobalIndex ], stsv.values[my_chp.ElectricityOutputC.GlobalIndex ], stsv.values[ my_chp.FuelDeliveredC.GlobalIndex ])
        
    assert stsv.values[ my_chp.ThermalEnergyDeliveredC.GlobalIndex ] == 3000
    assert stsv.values[my_chp.ElectricityOutputC.GlobalIndex ] == 2000
    assert stsv.values[ my_chp.FuelDeliveredC.GlobalIndex ] > 4e-5
    
    # #test if chp shuts down when too little hydrogen in storage and electricty as well as heat needed
    stsv.values[ electricity_target.GlobalIndex ] == 2.5e3
    stsv.values[ hydrogensoc.GlobalIndex ] = 0
    stsv.values[ l2_devicesignal.GlobalIndex ] = 1
    
    for tt in range( t, t + int( ( my_chp_controller_config.min_operation_time / seconds_per_timestep ) + 2 ) ):
        my_chp_controller.i_simulate( tt, stsv,  False )
        my_chp.i_simulate( tt, stsv, False )

    assert stsv.values[ my_chp.ThermalEnergyDeliveredC.GlobalIndex ] == 0
    assert stsv.values[my_chp.ElectricityOutputC.GlobalIndex ] == 0
    assert stsv.values[ my_chp.FuelDeliveredC.GlobalIndex ] == 0
    
    #test if chp shuts down when hydrogen is ok, electricity is needed, but heat not
    stsv.values[ electricity_target.GlobalIndex ] = 2.5e3
    stsv.values[ hydrogensoc.GlobalIndex ] = 50
    stsv.values[ l2_devicesignal.GlobalIndex ] = 1
    
    for ttt in range( tt, tt + int( ( my_chp_controller_config.min_idle_time / seconds_per_timestep ) + 2 ) ):
        my_chp_controller.i_simulate( ttt, stsv,  False )
        my_chp.i_simulate( ttt, stsv, False )
        
    stsv.values[ electricity_target.GlobalIndex ] = 2.5e3
    stsv.values[ hydrogensoc.GlobalIndex ] = 50
    stsv.values[ l2_devicesignal.GlobalIndex ] = 0
    
    for it in range( ttt, ttt + int( ( my_chp_controller_config.min_operation_time / seconds_per_timestep ) + 2 ) ):
        my_chp_controller.i_simulate( it, stsv,  False )
        my_chp.i_simulate( it, stsv, False )

    assert stsv.values[ my_chp.ThermalEnergyDeliveredC.GlobalIndex ] == 0
    assert stsv.values[my_chp.ElectricityOutputC.GlobalIndex ] == 0
    assert stsv.values[ my_chp.FuelDeliveredC.GlobalIndex ] == 0
    
    #test if chp shuts down when hydrogen is ok, heat is needed, but electricity not
    stsv.values[ electricity_target.GlobalIndex ] = 2.5e3
    stsv.values[ hydrogensoc.GlobalIndex ] = 50
    stsv.values[ l2_devicesignal.GlobalIndex ] = 1
    
    for t in range( it, it + int( ( my_chp_controller_config.min_idle_time / seconds_per_timestep ) + 2 ) ):
        my_chp_controller.i_simulate( t, stsv,  False )
        my_chp.i_simulate( t, stsv, False )
        
    stsv.values[ electricity_target.GlobalIndex ] = 0
    stsv.values[ hydrogensoc.GlobalIndex ] = 50
    stsv.values[ l2_devicesignal.GlobalIndex ] = 1
    
    for tt in range( t, t + int( ( my_chp_controller_config.min_operation_time / seconds_per_timestep ) + 2 ) ):
        my_chp_controller.i_simulate( tt, stsv,  False )
        my_chp.i_simulate( tt, stsv, False )

    assert stsv.values[ my_chp.ThermalEnergyDeliveredC.GlobalIndex ] == 0
    assert stsv.values[my_chp.ElectricityOutputC.GlobalIndex ] == 0
    assert stsv.values[ my_chp.FuelDeliveredC.GlobalIndex ] == 0