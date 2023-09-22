
from __future__ import annotations

import inspect
import json
import logging
from abc import ABC, abstractmethod
from collections.abc import MutableSequence
from contextlib import suppress
from datetime import datetime
from functools import wraps
from typing import Any, Callable

import numpy as np
import qcodes as qc
from qcodes import Station
from qcodes.dataset import AbstractSweep, LinSweep
from qcodes.dataset.dond.do_nd_utils import ActionsT
from qcodes.parameters import Parameter, ParameterBase

from qumada.instrument.buffers.buffer import is_bufferable, is_triggerable
from qumada.metadata import Metadata
from qumada.utils.ramp_parameter import ramp_or_set_parameter
from qumada.utils.utils import flatten_array

logger = logging.getLogger(__name__)

def is_measurement_script(o):
    return inspect.isclass(o) and issubclass(o, MeasurementScript)


class QtoolsDevice():
    def __init__(self):
        self.terminals = {}
        self.gate_parameters = {} #For the mapping, has to be renamed!
    
    def add_terminal(self, terminal_name, type: str|None = None):
        if terminal_name not in self.terminals.keys():
            self.__dict__[terminal_name] = self.terminals[terminal_name] = Terminal(terminal_name, self, type)
        else:
            raise Exception(f"Terminal {terminal_name} already exists. Please remove it first!")
    
    def remove_terminal(self, terminal_name):
        if terminal_name in self.terminals.keys():
            del self.__dict__[terminal_name]
            del self.terminals[terminal_name]
        else:
            logger.warning(f"{terminal_name} does not exist and could not be deleted")


    def load_from_dict(dictionary: dict):
        pass
    
    def save_to_dict(dictionary: dict):
        pass


def create_hook(func, hook):
    """
    Decorator to hook a function onto an existing function.
    The hook function can use keyword-only arguments, which are omitted prior to execution of the main function.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        hook(*args, **kwargs)
        # remove arguments used in hook from kwargs
        sig = inspect.signature(hook)
        varkw = next(
            filter(
                lambda p: p.kind is inspect.Parameter.VAR_KEYWORD,
                sig.parameters.values(),
            )
        ).name
        unused_kwargs = sig.bind(*args, **kwargs).arguments.get(varkw) or {}
        return func(*args, **unused_kwargs)

    return wrapper


class Terminal(ABC):
    """
    Base class for Terminals scripts.

    The abstract functions "reset" has to be implemented.
    """

    # TODO: Put list elsewhere! Remove names that were added as workarounds (e.g. aux_voltage) as soon as possible
    PARAMETER_NAMES: set[str] = {
        "voltage",
        "voltage_x_component",
        "voltage_y_component",
        "voltage_offset",
        "current",
        "current_x_component",
        "current_y_component",
        "current_compliance",
        "amplitude",
        "frequency",
        "output_enabled",
        "time_constant",
        "phase",
        "count",
        "aux_voltage_1",
        "aux_voltage_2",
        "temperature",
        "test_parameter",
    }

    def __init__(self, name, parent: QtoolsDevice|None=None, type: str|None=None):
        # Create function hooks for metadata
        # reverse order, so insert metadata is run second
        # self.run = create_hook(self.run, self._insert_metadata_into_db)
        # self.run = create_hook(self.run, self._add_data_to_metadata)
        # self.run = create_hook(self.run, self._add_current_datetime_to_metadata)

        self.properties: dict[Any, Any] = {}
        self.name = name
        self._parent = parent
        self.type = type
        self.terminal_parameters: dict[Any, dict[Any, Parameter | None] | Parameter | None] = {}

    def add_terminal_parameter(self, parameter_name: str, parameter: Parameter = None) -> None:
        """
        Adds a gate parameter to self.terminal_parameters.

        Args:
            parameter_name (str): Name of the parameter. Has to be in MeasurementScript.PARAMETER_NAMES.
            terminal_name (str): Name of the parameter's gate. Set this, if you want to define the parameter
                             under a specific gate. Defaults to None.
            parameter (Parameter): Custom parameter. Set this, if you want to set a custom parameter. Defaults to None.
        """
        if parameter_name not in Terminal.PARAMETER_NAMES:
            raise NameError(f'parameter_name "{parameter_name}" not in MeasurementScript.PARAMETER_NAMES.')
        if parameter_name not in self.terminal_parameters.keys():
            self.__dict__[parameter_name] = self.terminal_parameters[parameter_name] = Terminal_Parameter(parameter_name, self)
            if self.name not in self._parent.gate_parameters.keys():
                self._parent.gate_parameters[self.name] = {}
            self._parent.gate_parameters[self.name][parameter_name] = parameter
        else:
            raise Exception(f"Parameter{parameter_name} already exists")
        
    def remove_terminal_parameter(self, parameter_name: str, parameter: Parameter = None) -> None:
        """
        Adds a gate parameter to self.terminal_parameters.

        Args:
            parameter_name (str): Name of the parameter. Has to be in MeasurementScript.PARAMETER_NAMES.
            terminal_name (str): Name of the parameter's gate. Set this, if you want to define the parameter
                             under a specific gate. Defaults to None.
            parameter (Parameter): Custom parameter. Set this, if you want to set a custom parameter. Defaults to None.
        """
        if parameter_name in self.terminal_parameters.keys():
            del self.__dict__[parameter_name]
            del self.terminal_parameters[parameter_name]
        else:
            raise Exception(f"Parameter{parameter_name} does not exist!")



class Terminal_Parameter(ABC):
    def __init__(self, name: str, Terminal: Terminal) -> None:
        self._parent = Terminal
        self.properties: Dict[Any, Any] = {}
        self.type = None
        self._value = None
        self.name = None
        self.limits = None
        self._rampable = False
        self.default_value = None
        self.scaling = None
        self.instrument_parameter = None

    def reset(self):
        pass

    @property
    def value(self):
        return self._value
    
    @value.setter
    def value(self, value):
        if self.limits == None:
            self._value = value
        else:
            raise Exception("Limits are not yet implemented!")

    @value.getter
    def value(self):
        return self._value

    def ramp(self, value, ramp_rate):
        pass

    def __call__(self, value = None):
        if value == None:
            return self.value
        else:
            self.value=value



