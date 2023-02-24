"""
Created on Tue Dec  6 17:16:04 2022

@author: lab2
"""

import numpy as np
from qcodes.instrument.parameter import Parameter
from qcodes.instrument_drivers.Harvard.Decadac import Decadac

from qtools.instrument.mapping import DECADAC_MAPPING
from qtools.instrument.mapping.base import InstrumentMapping


class DecadacMapping(InstrumentMapping):
    def __init__(self):
        super().__init__(DECADAC_MAPPING)

    def ramp(
        self,
        parameters: list[Parameter],
        *,
        start_values: list[float] | None = None,
        end_values: list[float],
        ramp_time: float,
        block: bool = False,
        sync_trigger=None,
        sync_trigger_level=1,
    ) -> None:
        assert len(parameters) == len(end_values)
        if start_values is not None:
            assert len(parameters) == len(start_values)

        if len(parameters) > 1:
            raise Exception("Maximum length of rampable parameters currently is 1.")
        # TODO: Test delay when ramping multiple parameters in parallel.
        # TODO: Add Trigger option?
        # check, if all parameters are from the same instrument
        instruments = {parameter.root_instrument for parameter in parameters}
        if len(instruments) > 1:
            raise Exception("Parameters are from more than one instrument. This would lead to non synchronized ramps.")

        instrument: Decadac = instruments.pop()
        assert isinstance(instrument, Decadac)

        if not start_values:
            start_values = [param.get() for param in parameters]
        ramp_rates = np.abs((np.array(end_values) - np.array(start_values)) / np.array(ramp_time))
        if sync_trigger:
            if sync_trigger in parameters:
                raise Exception("Synchronized trigger cannot be part of parameters")
            assert isinstance(sync_trigger.root_instrument, Decadac)
            sync_trigger._instrument.enable_ramp(False)
            sync_trigger.set(sync_trigger_level)
        for param, end_value, ramp_rate in zip(parameters, end_values, ramp_rates):
            param._instrument._ramp(end_value, ramp_rate, block=block)
        if sync_trigger:
            sync_trigger.set(0)

    def trigger(self, parameter, level=1) -> None:
        instrument: Decadac = parameter.root_instrument
        assert isinstance(instrument, Decadac)
        parameter._instrument.enable_ramp(False)
        parameter.volt.set(level)