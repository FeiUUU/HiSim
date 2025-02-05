# -*- coding: utf-8 -*-
"""
Created on Thu Jul 21 20:04:59 2022

@author: Johanna
"""

from hisim import component as cp
from tests import functions_for_testing as fft
from hisim import loadtypes as lt

from hisim.simulationparameters import SimulationParameters
from hisim.components import generic_electrolyzer

def test_chp_system():

    seconds_per_timestep = 60
    my_simulation_parameters = SimulationParameters.one_day_only( 2017, seconds_per_timestep )
    
    my_electrolyzer_config = generic_electrolyzer.Electrolyzer.get_default_config( )
    my_electrolyzer = generic_electrolyzer.Electrolyzer( config = my_electrolyzer_config,
                                                         my_simulation_parameters = my_simulation_parameters )
    my_electrolyzer_controller_config = generic_electrolyzer.L1_Controller.get_default_config( )
    my_electrolyzer_controller = generic_electrolyzer.L1_Controller( config = my_electrolyzer_controller_config,
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
    
    number_of_outputs = fft.get_number_of_outputs( [ my_electrolyzer, my_electrolyzer_controller, electricity_target, hydrogensoc ] )
    stsv: cp.SingleTimeStepValues = cp.SingleTimeStepValues( number_of_outputs )

    my_electrolyzer_controller.l2_ElectricityTargetC.SourceOutput = electricity_target
    my_electrolyzer_controller.HydrogenSOCC.SourceOutput = hydrogensoc
    my_electrolyzer.ElectricityTargetC.SourceOutput = my_electrolyzer_controller.ElectricityTargetC

    # Add Global Index and set values for fake Inputs
    fft.add_global_index_of_components( [ my_electrolyzer, my_electrolyzer_controller, electricity_target, hydrogensoc ] )

    #test if electrolyzer runs when hydrogen in storage and electricty available
    stsv.values[ electricity_target.GlobalIndex ] = 1.8e3
    stsv.values[ hydrogensoc.GlobalIndex ] = 50
    
    for t in range( int( ( my_electrolyzer_controller_config.min_idle_time / seconds_per_timestep ) + 2 ) ):
        my_electrolyzer_controller.i_simulate( t, stsv,  False )
        my_electrolyzer.i_simulate( t, stsv, False )

    assert stsv.values[ my_electrolyzer.ElectricityOutputC.GlobalIndex ] == 1.8e3
    assert stsv.values[ my_electrolyzer.HydrogenOutputC.GlobalIndex ] > 5e-5
    
    #test if electrolyzer shuts down when too much hydrogen in storage and electricty available
    stsv.values[ electricity_target.GlobalIndex ] = 1.8e3
    stsv.values[ hydrogensoc.GlobalIndex ] = 99
    
    for tt in range( t, t + int( ( my_electrolyzer_controller_config.min_operation_time / seconds_per_timestep ) + 2 ) ):
        my_electrolyzer_controller.i_simulate( tt, stsv,  False )
        my_electrolyzer.i_simulate( tt, stsv, False )

    assert stsv.values[ my_electrolyzer.ElectricityOutputC.GlobalIndex ] == 0
    assert stsv.values[ my_electrolyzer.HydrogenOutputC.GlobalIndex ] == 0
    
    #test if electrolyzer shuts down when hydrogen is ok, but no electricity available
    stsv.values[ electricity_target.GlobalIndex ] = 1.8e3
    stsv.values[ hydrogensoc.GlobalIndex ] = 50
    
    for ttt in range( tt, tt + int( ( my_electrolyzer_controller_config.min_idle_time / seconds_per_timestep ) + 2 ) ):
        my_electrolyzer_controller.i_simulate( ttt, stsv,  False )
        my_electrolyzer.i_simulate( ttt, stsv, False )
        
    stsv.values[ electricity_target.GlobalIndex ] = 0
    stsv.values[ hydrogensoc.GlobalIndex ] = 50
    
    for it in range( ttt, ttt + int( ( my_electrolyzer_controller_config.min_operation_time / seconds_per_timestep ) + 2 ) ):
        my_electrolyzer_controller.i_simulate( it, stsv,  False )
        my_electrolyzer.i_simulate( it, stsv, False )

    assert stsv.values[ my_electrolyzer.ElectricityOutputC.GlobalIndex ] == 0
    assert stsv.values[ my_electrolyzer.HydrogenOutputC.GlobalIndex ] == 0