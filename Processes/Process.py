#!/usr/bin/env python3

import logging
from Processes import GraphProcess


class ProcessFactory(object):
    """Asset factor for the creating of Asset concrete objects

    """
    def __init__(self, module_name):

        self.module_name = module_name

    def factory(self, config_dict):
        """ Factory function for Asset Class objects

        :param config_dict: Configuration dictonary
        :return factory_class: Process Class decendent of type listed in config_dict
        """
        class_type = config_dict['model_config']['class_name'] # TODO: This sucks re-write tomorrow morning.
        new_module = __import__(self.module_name)
        new_pclass = getattr(new_module , 'Process')
        new_class = getattr(new_pclass, class_type)
        return new_class(config_dict)


class ProcessContainer(object):
    def __init__(self):
        self._process_list = list()
        self._process_dict = dict()
        self._ready = False

    @property
    def process_list(self):
        return self._process_list

    @property
    def process_dict(self):
        return self._process_dict

    @property
    def ready(self):
        return self._ready

    def add_process(self, new_process):
        self._ready = False
        self._process_dict.update({new_process.name: new_process})
        self._process_list.append(new_process)

    def sort(self, system):
        temp_graph = GraphProcess.GraphProcess(self)
        temp_graph.build_adj_list()
        process_names_topo_sort = GraphProcess.DFS(temp_graph).topological_sort

        self._process_list = []
        for process_name in process_names_topo_sort:
            self._process_list.append(self.process_dict[process_name])

        self._ready = True

    def run(self, handle):
        if self._ready:
            for process in self._process_list:
                process.run(handle)
        else:
            print('Process Module not Ready')


class ProcessInterface(object):
    def __init__(self):
        self._input = dict()
        self._output = dict()
        self._config = dict()
        self._name = 'UNDEFINED'

    @property
    def input(self):
        return self._input

    @property
    def output(self):
        return self._output

    @property
    def config(self):
        return self._config

    @property
    def name(self):
        return self._name

    def init_process(self, config_dict):
        for key, val in config_dict['model_config'].items():
            if key in self.config.keys():
                self.config[key] = val

    def run(self, handle):
        self.read_input(handle)
        self.do_work()
        self.write_output(handle)
        return

    def read_input(self, handle):
        self._input = handle.read(self.input)

    def write_output(self, handle):
        for key, val in self.output.items():
            handle.write(key, val)
        return

    def do_work(self):
        return


class SingleProcess(ProcessInterface):
    def __init__(self):
        super(SingleProcess, self).__init__()


class AggregateProcess(ProcessInterface):
    def __init__(self, process_list):
        super(AggregateProcess, self).__init__()

        self._process_list = process_list

        for process in self._process_list:
            self._input.update(process._input)

    def run(self, handle):
        self.do_work()
        self.write_output(handle)


class INV_SOC_PWR_CTRL(SingleProcess):
    def __init__(self, config_dict):
        super(INV_SOC_PWR_CTRL, self).__init__()
        self.init_process(config_dict)

        self._name = 'inverter soc power controller'
        self._input.update({'inverter_soc': 0})
        self._config.update({'inverter_target_soc': 0})
        self._output.update({'inverter_kw_setpoint': None})

        logging.debug('PROCESS MODULE INTERFACE: %s constructed', self.name)

    def do_work(self):
        if self._input['inverter_soc'] < self.config['inverter_target_soc']:
            self._output['inverter_kw_setpoint'] = -50
        elif self._input['inverter_soc'] > self.config['inverter_target_soc']:
            self._output['inverter_kw_setpoint'] = 50

    def __del__(self):
        logging.debug('PROCESS MODULE INTERFACE: %s deconstructed', self.name)


class INV_DMDLMT_PWR_CTRL(SingleProcess):
    def __init__(self, config_dict):
        super(INV_DMDLMT_PWR_CTRL, self).__init__()
        self.init_process(config_dict)

        self._name = 'inverter demand limiting power controller'
        self._input.update({'grid_kw': 0})
        self._config.update({'grid_kw_export_limit': 0,
                            'grid_kw_import_limit': 0})
        self._output.update({'inverter_kw_setpoint': None})

        logging.debug('PROCESS MODULE INTERFACE: %s constructed', self.name)

    def do_work(self):

        if self._input['grid_kw'] < 0 and abs(self._input['grid_kw']) > self._config['grid_kw_export_limit']:
            self._output['inverter_kw_setpoint'] =  self._config['grid_kw_export_limit'] + self._input['grid_kw']

        elif self._input['grid_kw'] > self._config['grid_kw_import_limit']:
            self._output['inverter_kw_setpoint'] = self._input['grid_kw'] - self._config['grid_kw_import_limit']

        else:
            self._output['inverter_kw_setpoint'] = 0

    def __del__(self):
        logging.debug('PROCESS MODULE INTERFACE: %s deconstructed', self.name)


class INV_UPT_STATUS(SingleProcess):
    def __init__(self, config_dict):
        super(INV_UPT_STATUS, self).__init__()
        self.init_process(config_dict)

        self._name = 'inverter update status'
        self._input = dict()   # No input, acts as root nodes
        self._config.update({'asset_ref': None})  # TODO: asset_ref in update status process, or use asset directly?
        self._output.update({'inverter_soc': None,
                            'inverter_kw': None})

        logging.debug('PROCESS MODULE INTERFACE: %s constructed', self.name)

    def do_work(self):
        ''' Call on asset to update tagbus from self

        '''
        self._output['inverter_soc'] = 0.5
        self._output['inverter_kw'] = 0.0

    def __del__(self):
        logging.debug('PROCESS MODULE INTERFACE: %s deconstructed', self.name)


class INV_WRT_CTRL(SingleProcess):
    def __init__(self, config_dict):
        super(INV_WRT_CTRL, self).__init__()
        self.init_process(config_dict)

        self._name = 'inverter write control'
        self._input.update({'inverter_kw_setpoint': 0})
        self._config.update({'asset_ref': None})
        self._output = dict()

        logging.debug('PROCESS MODULE INTERFACE: %s constructed', self.name)

    def do_work(self):
        """ Call Write Tagbus to Asset

        """
        pass

    def __del__(self):
        logging.debug('PROCESS MODULE INTERFACE: %s deconstructed', self.name)


class GRID_UPT_STATUS(SingleProcess):
    def __init__(self, config_dict):
        super(GRID_UPT_STATUS, self).__init__()
        self.init_process(config_dict)

        self._name = 'grid update status'
        self._input = dict()  # Empty input, acts as root node
        self._config.update({'asset_ref': None})
        self._output.update({'grid_kw': None})

        logging.debug('PROCESS MODULE INTERFACE: %s constructed', self.name)

    def do_work(self):
        self._output['grid_kw'] = 100

    def __del__(self):
        logging.debug('PROCESS MODULE INTERFACE: %s deconstructed', self.name)


class AggregateProcessSummation(AggregateProcess):
    def __init__(self, process_list):
        super(AggregateProcessSummation, self).__init__(process_list)

        self._name = 'aggregate process summation'

        logging.debug('PROCESS MODULE INTERFACE: %s constructed', self.name)

    def do_work(self):
        summation = dict()
        for process in self._process_list:
            process.do_work()
            for key, val in process._output.items():
                try:
                    summation[key] += val
                except:
                    summation[key] = val
        self._output = summation

    def __del__(self):
        logging.debug('PROCESS MODULE INTERFACE: %s deconstructed', self.name)