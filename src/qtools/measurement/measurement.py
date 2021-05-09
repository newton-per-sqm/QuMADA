#!/usr/bin/env python3
"""
Measurement
"""

from dataclasses import dataclass, field
from typing import MutableSequence, Mapping

from qcodes import Station, Parameter

from qtools.data.measurement import EquipmentInstance, FunctionType


class QtoolsStation(Station):
    """Station object, inherits from qcodes Station."""


class VirtualGate():
    """Virtual Gate"""
    def __init__(self):
        self._functions = []

    @property
    def functions(self):
        """List of equipment Functions, the virtual gate shall have."""
        return self._functions

    @functions.setter
    def functions(self, functions: MutableSequence):
        self._functions = functions


class VirtualParameter():
    pass


@dataclass
class FunctionMapping():
    """Data structure, that holds the mapping of several instrument parameters
    that correspond to one specific FunctionType.
    """
    name: str
    function_type: FunctionType
    gate: VirtualGate
    parameters: Mapping[Parameter] = field(default_factory=dict)


class ExperimentHandler():
    """Experiment Handler"""
    def __init__(self, station: Station = None,
                 equipmentInstances: MutableSequence[EquipmentInstance] = None) -> None:
        if equipmentInstances is None:
            equipmentInstances = []

        if station:
            self._station = station
        else:
            self._station = Station()

        for instance in equipmentInstances:
            self._load_instrument(instance)

    def _load_instrument(self, instance: EquipmentInstance):
        pass
