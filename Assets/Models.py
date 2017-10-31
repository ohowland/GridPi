#!/usr/bin/env python3

class AssetFactory(object):
    """Asset factor for the creating of Asset concrete objects

    """
    def __init__(self, module_name):

        self.module_name = module_name

    def factory(self, config_dict):
        """ Factory function for Asset Class objects

        :param config_dict: Configuration dictonary
        :return factory_class: Asset Class decendent of type listed in config_dict
        """
        class_type = config_dict['model_config']['class_name']
        new_module = __import__(self.module_name + '.' + class_type, fromlist=[type])
        new_class = getattr(new_module, class_type)
        return new_class(config_dict)

class Asset(object):
    """Basic asset in power system.
       All physical devices in the system are considered 'Asset' objects
    """
    def __init__(self):

        # Asset Configuration:
        self.config = dict()
        self.status = dict()
        self.ctrl = dict()

        self.config.update({'name' : None,
                            'class_name': None,
                            'freq_rated': None,
                            'volt_rated': None,
                            'cap_kva_rated': 0.0,
                            'cap_kw_pos_rated': 0.0,
                            'cap_kw_neg_rated': 0.0,
                            'cap_kvar_neg_rated': 0.0,
                            'cap_kvar_pos_rated': 0.0,
                            'comm_interface': None})  # Communications Interface Object

        self.status.update({'freq': 0.0,
                            'volt': 0.0,
                            'kw': 0.0,
                            'kvar': 0.0,
                            'cap_kw_pos_avail': 0.0,
                            'cap_kw_neg_avail': 0.0,
                            'cap_kvar_pos_avail': 0.0,
                            'cap_kvar_neg_avail': 0.0,
                            'alarm': False,
                            'warning': False,
                            'caution': False,
                            'online': False,
                            'on_system': False})

    def init_model(self, config_dict):
        for key, val in config_dict['model_config'].items():
            if key in self.config.keys():
                self.config[key] = val

    def update(self):
        for key in self.__dict__.keys():
            if key in self.config['comm_interface'].cvt.keys():
                self.__dict__[key] = self.config['comm_interface'].cvt[key]

class CtrlAsset(Asset):
    """CtrlAsset is an extension of the Asset class.
       These devices can be controlled
    """
    def __init__(self):
        super(CtrlAsset, self).__init__()

        # CtrlAsset Configuration
        # ...

        # CtrlAsset Status
        self.status.update({'enabled' : False,
                            'remote_ctrl' : False})

        # CtrlAsset Control
        self.ctrl.update({'enable' : False,
                          'run' : False,
                          'clear_faults' : False})

    def update(self):

        super(CtrlAsset, self).update()

        self.status['cap_kw_pos_avail'] = self.config['cap_kw_pos_rated'] * self.ctrl['enabled']
        self.status['cap_kw_neg_avail'] = self.config['cap_kw_neg_rated'] * self.ctrl['enabled']
        self.status['cap_kvar_pos_avail'] = self.config['cap_kvar_pos_rated'] * self.ctrl['enabled']
        self.status['cap_kvar_neg_avail'] = self.config['cap_kvar_neg_rated'] * self.ctrl['enabled']


class GridIntertie(CtrlAsset):
    """Grid intertie archetype object

    """
    def __init__(self):
        super(GridIntertie, self).__init__()

    def update(self):
        super(GridIntertie, self).update()


class EnergyStorage(CtrlAsset):
    """Energy Storage archetype object

    """
    def __init__(self):
        super(EnergyStorage, self).__init__()
        self.status.update({'soc': 0,
                            'kw_setpoint': 0.0})

    def update(self):
        super(EnergyStorage, self).update()


class Feeder(CtrlAsset):
    """Feeder archetype object

    """
    def __init__(self):
        super(Feeder, self).__init__()

    def update(self):
        super(Feeder, self).update()