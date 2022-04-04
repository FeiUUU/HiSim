# Generic/Built-in

# Owned
import copy
import numpy as np
import component as cp
import loadtypes as lt


__authors__ = "Maximilian"
__copyright__ = "Copyright 2021, the House Infrastructure Project"
__credits__ = ["Noah Pflugradt"]
__license__ = ""
__version__ = ""
__maintainer__ = "Maximilian Hillen"
__email__ = "vitor.zago@rwth-aachen.de"
__status__ = "development"

class ControllerState:
    def __init__(self, control_signal_gas_heater: float, control_signal_chp: float, control_signal_heat_pump: int,temperature_storage_target_ww_C: float,temperature_storage_target_hw_C: float,timestep_of_hysteresis_ww:int,timestep_of_hysteresis_hw:int):
        self.control_signal_gas_heater = control_signal_gas_heater
        self.control_signal_chp = control_signal_chp
        self.control_signal_heat_pump = control_signal_heat_pump
        self.temperature_storage_target_ww_C=temperature_storage_target_ww_C
        self.temperature_storage_target_hw_C=temperature_storage_target_hw_C
        self.timestep_of_hysteresis_ww = timestep_of_hysteresis_ww
        self.timestep_of_hysteresis_hw = timestep_of_hysteresis_hw


class Controller(cp.Component):
    """
    Connects energysystemcomponents,
    calculates Control Signals of Components,
    rules workflow battery
    4 strategies can be choosen:
    "optimize_own_consumption"
    "seasonal_storage"
    "peak_shaving_into_grid"
    "peak_shaving_from_grid"
    """
    #Inputs
    ElectricityConsumptionBuilding="ElectricityConsumptionBuilding"
    StorageTemperatureHeatingWater = "StorageTemperatureHeatingWater"
    StorageTemperatureWarmWater = "StorageTemperatureWarmWater"

    ElectricityOutputPvs = "ElectricityOutputPvs"
    ElectricityDemandHeatPump= "ElectricityDemandHeatPump"
    ElectricityToOrFromBatteryReal = "ElectricityToOrFromBatteryReal"
    ElectricityToElectrolyzerUnused = "ElectricityToElectrolyzerUnused"
    ElectricityFromCHPReal = "ElectricityFromCHPReal"


    # Outputs
    ElectricityToElectrolyzerTarget="ElectricityToElectrolyzerTarget"
    ElectricityToOrFromBatteryTarget="ElectricityToOrFromBatteryTarget"
    ElectricityFromCHPTarget="ElectricityFromCHPTarget"
    ElectricityToOrFromGrid="ElectricityToOrFromGrid"

    ControlSignalGasHeater="ControlSignalGasHeater"
    ControlSignalChp="ControlSignalChp"
    ControlSignalHeatPump="ControlSignalHeatPump"
    ControlSignalChooseStorage="ControlSignalChooseStorage"

    CheckPeakShaving="CheckPeakShaving"

    def __init__(self,
                 temperature_storage_target_warm_water = 50,
                 temperature_storage_target_heating_water =35,
                 temperature_storage_target_hysteresis_ww=45,
                 temperature_storage_target_hysteresis_hw=30,
                 strategy = "optimize_own_consumption",
                 limit_to_shave=0,
                 percentage_to_shave=0):
        super().__init__("Controller")

        self.temperature_storage_target_warm_water=temperature_storage_target_warm_water
        self.temperature_storage_target_heating_water=temperature_storage_target_heating_water
        self.temperature_storage_target_hysteresis_hw=temperature_storage_target_hysteresis_hw
        self.temperature_storage_target_hysteresis_ww=temperature_storage_target_hysteresis_ww
        self.strategy=strategy
        #strategy=["optimize_own_consumption","peak_shaving_from_grid", "peak_shaving_into_grid","seasonal_storage"]
        self.limit_to_shave= limit_to_shave
        self.state = ControllerState(control_signal_heat_pump=0,
                                     control_signal_gas_heater=0,
                                     control_signal_chp=0,
                                     temperature_storage_target_ww_C=self.temperature_storage_target_warm_water,
                                     temperature_storage_target_hw_C = self.temperature_storage_target_heating_water,
                                     timestep_of_hysteresis_ww=0,
                                     timestep_of_hysteresis_hw=0)
        self.previous_state = copy.copy(self.state)
        ###Inputs

        self.temperature_storage_warm_water: cp.ComponentInput = self.add_input(self.ComponentName,
                                                                     self.StorageTemperatureWarmWater,
                                                                     lt.LoadTypes.Water,
                                                                     lt.Units.Celsius,
                                                                     False)
        self.temperature_storage_heating_water: cp.ComponentInput = self.add_input(self.ComponentName,
                                                                     self.StorageTemperatureHeatingWater,
                                                                     lt.LoadTypes.Water,
                                                                     lt.Units.Celsius,
                                                                     False)

        self.electricity_consumption_building: cp.ComponentInput = self.add_input(self.ComponentName,
                                                                                  self.ElectricityConsumptionBuilding,
                                                                                  lt.LoadTypes.Electricity,
                                                                                  lt.Units.Watt,
                                                                                  False)

        self.electricity_output_pvs: cp.ComponentInput = self.add_input(self.ComponentName,
                                                                        self.ElectricityOutputPvs,
                                                                        lt.LoadTypes.Electricity,
                                                                        lt.Units.Watt,
                                                                        True)

        self.electricity_to_or_from_battery_real: cp.ComponentInput = self.add_input(self.ComponentName,
                                                                              self.ElectricityToOrFromBatteryReal,
                                                                              lt.LoadTypes.Electricity,
                                                                              lt.Units.Watt,
                                                                              False)
        self.electricity_to_electrolyzer_unused: cp.ComponentInput = self.add_input(self.ComponentName,
                                                                              self.ElectricityToElectrolyzerUnused,
                                                                              lt.LoadTypes.Electricity,
                                                                              lt.Units.Watt,
                                                                              False)
        self.electricity_from_chp_real: cp.ComponentInput = self.add_input(self.ComponentName,
                                                                              self.ElectricityFromCHPReal,
                                                                              lt.LoadTypes.Electricity,
                                                                              lt.Units.Watt,
                                                                              False)
        self.electricity_demand_heat_pump: cp.ComponentInput = self.add_input(self.ComponentName,
                                                                              self.ElectricityDemandHeatPump,
                                                                              lt.LoadTypes.Electricity,
                                                                              lt.Units.Watt,
                                                                              False)

        # Outputs

        self.electricity_to_or_from_grid: cp.ComponentOutput = self.add_output(self.ComponentName,
                                                                       self.ElectricityToOrFromGrid,
                                                                       lt.LoadTypes.Electricity,
                                                                       lt.Units.Watt,
                                                                       False)
        self.electricity_from_chp_target: cp.ComponentOutput = self.add_output(self.ComponentName,
                                                                         self.ElectricityFromCHPTarget,
                                                                         lt.LoadTypes.Electricity,
                                                                         lt.Units.Watt,
                                                                         False)
        self.electricity_to_electrolyzer_target: cp.ComponentOutput = self.add_output(self.ComponentName,
                                                                         self.ElectricityToElectrolyzerTarget,
                                                                         lt.LoadTypes.Electricity,
                                                                         lt.Units.Watt,
                                                                         False)
        self.electricity_to_or_from_battery_target: cp.ComponentOutput = self.add_output(self.ComponentName,
                                                                         self.ElectricityToOrFromBatteryTarget,
                                                                         lt.LoadTypes.Electricity,
                                                                         lt.Units.Watt,
                                                                         False)
        self.control_signal_gas_heater: cp.ComponentOutput = self.add_output(self.ComponentName,
                                                                         self.ControlSignalGasHeater,
                                                                         lt.LoadTypes.Any,
                                                                         lt.Units.Percent,
                                                                         False)
        self.control_signal_chp: cp.ComponentOutput = self.add_output(self.ComponentName,
                                                                         self.ControlSignalChp,
                                                                         lt.LoadTypes.Any,
                                                                         lt.Units.Percent,
                                                                         False)
        self.control_signal_heat_pump: cp.ComponentOutput = self.add_output(self.ComponentName,
                                                                         self.ControlSignalHeatPump,
                                                                         lt.LoadTypes.Any,
                                                                         lt.Units.Percent,
                                                                         False)
        self.check_peak_shaving: cp.ComponentOutput = self.add_output(self.ComponentName,
                                                                         self.CheckPeakShaving,
                                                                         lt.LoadTypes.Any,
                                                                         lt.Units.Any,
                                                                         False)
        self.control_signal_choose_storage: cp.ComponentOutput = self.add_output(self.ComponentName,
                                                                         self.ControlSignalChooseStorage,
                                                                         lt.LoadTypes.Any,
                                                                         lt.Units.Any,
                                                                         False)

    def build(self, mode):
        self.mode = mode

    def write_to_report(self):
        pass

    def i_save_state(self):
        #abändern, siehe Storage
        pass
        self.previous_state = self.state

    def i_restore_state(self):
        pass
        self.state = self.previous_state

    def i_doublecheck(self, timestep: int, stsv: cp.SingleTimeStepValues):
        pass


    def optimize_own_consumption(self, delta_demand: float, stsv: cp.SingleTimeStepValues):

        electricity_to_or_from_battery_target = 0
        electricity_from_chp_target = 0
        electricity_to_or_from_grid = 0

        # Check if Battery is Component of Simulation
        if self.electricity_to_or_from_battery_real.SourceOutput is not None:
            electricity_to_or_from_battery_target = delta_demand

        # electricity_not_used_battery of Charge or Discharge
        electricity_not_used_battery = electricity_to_or_from_battery_target - stsv.get_input_value(
            self.electricity_to_or_from_battery_real)
        #more electricity than needed
        if delta_demand > 0:
            # Negative sign, because Electricity will flow into grid->Production of Electricity
            electricity_to_or_from_grid = -delta_demand + stsv.get_input_value(self.electricity_to_or_from_battery_real)

        elif delta_demand < 0:

            if delta_demand - electricity_to_or_from_battery_target + electricity_not_used_battery < 0 and self.electricity_from_chp_real.SourceOutput is not None:
                electricity_from_chp_target = -delta_demand + stsv.get_input_value(
                    self.electricity_to_or_from_battery_real)

            # Positive sing, because Electricity will flow out of grid->Consumption of Electricity
            electricity_to_or_from_grid = -delta_demand + stsv.get_input_value(
                self.electricity_to_or_from_battery_real) - stsv.get_input_value(self.electricity_from_chp_real)

        stsv.set_output_value(self.electricity_to_or_from_grid, electricity_to_or_from_grid)
        stsv.set_output_value(self.electricity_from_chp_target, electricity_from_chp_target)
        stsv.set_output_value(self.electricity_to_or_from_battery_target, electricity_to_or_from_battery_target)


    #seasonal storaging is almost the same as own_consumption, but a electrolyzer is added
    #follows strategy to first charge battery than produce H2
    def seasonal_storage(self, delta_demand: float, stsv: cp.SingleTimeStepValues):

        electricity_to_or_from_battery_target = 0
        electricity_from_chp_target = 0
        electricity_to_or_from_grid = 0
        electricity_to_electrolyzer_target = 0

        # Check if Battery is Component of Simulation
        if self.electricity_to_or_from_battery_real.SourceOutput is not None:
            electricity_to_or_from_battery_target = delta_demand

        # electricity_not_used_battery of Charge or Discharge
        electricity_not_used_battery = electricity_to_or_from_battery_target - stsv.get_input_value(
            self.electricity_to_or_from_battery_real)
        # more electricity than needed
        if delta_demand > 0:
            # Check if enough electricity is there to charge CHP (finds real solution after 2 Iteration-Steps)
            if self.electricity_to_electrolyzer_unused.SourceOutput is not None:
                # possibility to  produce H2
                electricity_to_electrolyzer_target = delta_demand - stsv.get_input_value(
                    self.electricity_to_or_from_battery_real)
                if electricity_to_electrolyzer_target<0:
                    electricity_to_electrolyzer_target=0

            # Negative sign, because Electricity will flow into grid->Production of Electricity
            electricity_to_or_from_grid = -delta_demand + stsv.get_input_value(
                self.electricity_to_or_from_battery_real) + (electricity_to_electrolyzer_target-stsv.get_input_value(self.electricity_to_electrolyzer_unused))


        elif delta_demand < 0:

            if delta_demand - electricity_to_or_from_battery_target + electricity_not_used_battery < 0 and self.electricity_from_chp_real.SourceOutput is not None:
                electricity_from_chp_target = -delta_demand + stsv.get_input_value(
                    self.electricity_to_or_from_battery_real)

            # Positive sing, because Electricity will flow out of grid->Consumption of Electricity
            electricity_to_or_from_grid = -delta_demand + stsv.get_input_value(
                self.electricity_to_or_from_battery_real) - stsv.get_input_value(self.electricity_from_chp_real)

        stsv.set_output_value(self.electricity_to_or_from_grid, electricity_to_or_from_grid)
        stsv.set_output_value(self.electricity_from_chp_target, electricity_from_chp_target)
        stsv.set_output_value(self.electricity_to_electrolyzer_target, electricity_to_electrolyzer_target)
        stsv.set_output_value(self.electricity_to_or_from_battery_target, electricity_to_or_from_battery_target)

    def peak_shaving_from_grid(self,delta_demand:float,limit_to_shave: float,stsv: cp.SingleTimeStepValues):
        electricity_to_or_from_battery_target=0
        check_peak_shaving=0
        #More Elect. Produced than needed
        if delta_demand > 0:
            electricity_to_or_from_battery_target = delta_demand
            #Battery charged for all amount of deltademand
            if 0.95*delta_demand< stsv.get_input_value(self.electricity_to_or_from_battery_real) and 1.05 * delta_demand > stsv.get_input_value(self.electricity_to_or_from_battery_real):
                electricity_to_or_from_battery_target = delta_demand + 0.7*limit_to_shave
            elif stsv.get_input_value(self.electricity_to_or_from_battery_real) >= 1.05 * delta_demand:
                electricity_to_or_from_battery_target = delta_demand + 0.7*limit_to_shave
        # Less Elect. Produced than needed, Demand higher than Peak
        elif -delta_demand >  1.01*limit_to_shave:
            check_peak_shaving=1
            electricity_to_or_from_battery_target= delta_demand+1.05*limit_to_shave


        # Less Elect. Produced than needed, Demand smaller than Peak
        elif -delta_demand < limit_to_shave and -delta_demand>0:
            electricity_to_or_from_battery_target= -(-delta_demand -0.9 * limit_to_shave)

        electricity_to_or_from_grid = -delta_demand + stsv.get_input_value(
            self.electricity_to_or_from_battery_real)
        if electricity_to_or_from_grid<-1029.9*0.9 and electricity_to_or_from_grid>-1029.9*1.1:
            print("stop")
        stsv.set_output_value(self.electricity_to_or_from_grid, electricity_to_or_from_grid)
        stsv.set_output_value(self.electricity_to_or_from_battery_target, electricity_to_or_from_battery_target)
        stsv.set_output_value(self.check_peak_shaving, check_peak_shaving)

    def peak_shaving_into_grid(self,delta_demand:float,limit_to_shave: float,stsv: cp.SingleTimeStepValues):
        #Hier delta Demand noch die Leistung aus CHP hinzufügen
        electricity_to_or_from_battery_target=0
        check_peak_shaving=0

        if delta_demand > limit_to_shave:
            electricity_to_or_from_battery_target=delta_demand-limit_to_shave

            if delta_demand - limit_to_shave - stsv.get_input_value(
                self.electricity_to_or_from_battery_real) > 0:
                check_peak_shaving = delta_demand - limit_to_shave - stsv.get_input_value(
                self.electricity_to_or_from_battery_real) # Peak Shaving didnt work
            else:
                check_peak_shaving = 1
        elif delta_demand<0:
            electricity_to_or_from_battery_target=delta_demand

        electricity_to_or_from_grid=-delta_demand + stsv.get_input_value(
            self.electricity_to_or_from_battery_real)
        stsv.set_output_value(self.electricity_to_or_from_grid, electricity_to_or_from_grid)
        stsv.set_output_value(self.electricity_to_or_from_battery_target, electricity_to_or_from_battery_target)
        stsv.set_output_value(self.check_peak_shaving, check_peak_shaving)

    def simulate_storage(self,delta_temperature:float,stsv: cp.SingleTimeStepValues, timestep:int, temperature_storage:float, temperature_storage_target:float,temperature_storage_target_hysteresis:float,temperature_storage_target_C:float,timestep_of_hysteresis:int):
        # Idea of 2-Punkt-Regelung mit Hysterese
        control_signal_chp = 0
        control_signal_gas_heater = 0
        control_signal_heat_pump= 0
        temperature_storage_target_C=temperature_storage_target_C
        timestep_of_hysteresis=timestep_of_hysteresis

        # WaterStorage
        if temperature_storage > 0:
            if delta_temperature >= 10:
               control_signal_heat_pump = 1
               control_signal_chp = 1
               control_signal_gas_heater = 1
               temperature_storage_target_C = temperature_storage_target

            elif delta_temperature > 5 and delta_temperature < 10:
               # heat storage
               # look at state of signal of heating componentens
               # if signal was above zero put on more heating systems
               control_signal_heat_pump=1
               if self.state.control_signal_chp < 1:
                   control_signal_chp = 1
                   control_signal_gas_heater = 1
               elif self.state.control_signal_chp == 1:
                   control_signal_gas_heater = 1
               temperature_storage_target_C = temperature_storage_target

            elif delta_temperature > 0 and delta_temperature <= 5:
               control_signal_heat_pump = 1
               if self.state.control_signal_chp < 1:
                   control_signal_chp = 1
               elif self.state.control_signal_chp == 1:
                   control_signal_gas_heater = 0.5
               temperature_storage_target_C = temperature_storage_target

               # Storage warm enough. Try to turn off Heaters
            elif delta_temperature <= 0:

                if temperature_storage_target_C == temperature_storage_target and timestep_of_hysteresis != timestep:
                    temperature_storage_target_C = temperature_storage_target_hysteresis
                    timestep_of_hysteresis = timestep
                elif temperature_storage_target_C != temperature_storage_target and timestep_of_hysteresis != timestep:
                    control_signal_heat_pump = 0
                    control_signal_gas_heater = 0
                    control_signal_chp = 0

        self.state.control_signal_gas_heater = control_signal_gas_heater
        self.state.control_signal_chp = control_signal_chp
        self.state.control_signal_heat_pump = control_signal_heat_pump
        stsv.set_output_value(self.control_signal_heat_pump, control_signal_heat_pump)
        stsv.set_output_value(self.control_signal_gas_heater, control_signal_gas_heater)
        stsv.set_output_value(self.control_signal_chp, control_signal_chp)


        return temperature_storage_target_C, \
               timestep_of_hysteresis



    def i_simulate(self, timestep: int, stsv: cp.SingleTimeStepValues,seconds_per_timestep: int, force_convergence : bool):
        if force_convergence:
            return
        ###ELECTRICITY
        limit_to_shave=self.limit_to_shave
        # Production of Electricity positve sign
        # Consumption of Electricity negative sign
        delta_demand = stsv.get_input_value(self.electricity_output_pvs) - stsv.get_input_value(self.electricity_consumption_building) -stsv.get_input_value(self.electricity_demand_heat_pump)

        if self.strategy == "optimize_own_consumption":
            self.optimize_own_consumption(delta_demand=delta_demand,stsv=stsv)
        elif self.strategy == "seasonal_storage":
            self.seasonal_storage(delta_demand=delta_demand, stsv=stsv)
        elif self.strategy == "peak_shaving_into_grid":
            self.peak_shaving_into_grid(delta_demand=delta_demand, limit_to_shave=limit_to_shave,stsv=stsv)
        elif self.strategy == "peak_shaving_from_grid":
            self.peak_shaving_from_grid(delta_demand=delta_demand, limit_to_shave=limit_to_shave,stsv=stsv)




        #######HEAT########
        #Logic of regulating HeatDemand:
        #First heat up WarmWaterStorage->more important, than heat up HeatingWater
        #But only one Storage can be heated up in a TimeStep!

        #Simulate WarmWater

        delta_temperature_ww = self.state.temperature_storage_target_ww_C - stsv.get_input_value(self.temperature_storage_warm_water)
        delta_temperature_hw = self.state.temperature_storage_target_hw_C - stsv.get_input_value(self.temperature_storage_heating_water)
        #just happend in parameterstudies
        if delta_temperature_ww>=0 and delta_temperature_hw>=0:
            if delta_temperature_hw <= delta_temperature_ww:
                control_signal_choose_storage = 1
            else:
                control_signal_choose_storage = 2
        elif delta_temperature_ww<0 and delta_temperature_hw<0:
            if delta_temperature_hw <= delta_temperature_ww:
                control_signal_choose_storage = 1
            else:
                control_signal_choose_storage = 2
        elif delta_temperature_ww<=0 and delta_temperature_hw>=0:
            control_signal_choose_storage = 2
        elif delta_temperature_ww >= 0 and delta_temperature_hw <= 0:
            control_signal_choose_storage = 1
        if control_signal_choose_storage == 1:
            self.state.temperature_storage_target_ww_C, self.state.timestep_of_hysteresis_ww = self.simulate_storage(stsv=stsv,
                                                      delta_temperature=delta_temperature_ww,
                                                      timestep=timestep,
                                                      temperature_storage=stsv.get_input_value(self.temperature_storage_warm_water),
                                                      temperature_storage_target=self.temperature_storage_target_warm_water,
                                                      temperature_storage_target_hysteresis=self.temperature_storage_target_hysteresis_ww,
                                                      temperature_storage_target_C=self.state.temperature_storage_target_ww_C,
                                                      timestep_of_hysteresis=self.state.timestep_of_hysteresis_ww)
        elif control_signal_choose_storage == 2:
            delta_temperature_hw = self.state.temperature_storage_target_hw_C - stsv.get_input_value(self.temperature_storage_heating_water)
            self.state.temperature_storage_target_hw_C, self.state.timestep_of_hysteresis_hw = self.simulate_storage(stsv=stsv,
                                                      delta_temperature=delta_temperature_hw,
                                                      timestep=timestep,
                                                      temperature_storage=stsv.get_input_value(self.temperature_storage_heating_water),
                                                      temperature_storage_target=self.temperature_storage_target_heating_water,
                                                      temperature_storage_target_hysteresis=self.temperature_storage_target_hysteresis_hw,
                                                      temperature_storage_target_C=self.state.temperature_storage_target_hw_C,
                                                      timestep_of_hysteresis=self.state.timestep_of_hysteresis_hw)

        stsv.set_output_value(self.control_signal_choose_storage, control_signal_choose_storage)





