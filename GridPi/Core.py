#!/usr/bin/env python3

import logging
from Process import Process


class Tag(object):

    def __init__(self, name, value=None, units=None):
        self._name = name
        self._value = value
        self._units = units

    @property
    def name(self):
        return self._name

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        self._value = val

    @property
    def units(self):
        return self._units


class TagBus(object):

    def __init__(self):
        self._tags = dict()

    @property
    def tags(self):
        return self._tags

    def add(self, tag_name, default_value=None, units=None):
        if self._tags.get(tag_name, False):  # Statement executes if tag is found
            logging.warning('CORE: tagbus.add_tag(): Attempt to overwrite existing tag: "%s"', tag_name)
        else:                                  # Statement executes if tag is not found
            self._tags[tag_name] = Tag(tag_name, value=default_value, units=units)
            #logging.info('tagbus.add_tag(): %s tag added to tagbus', tag_name)

    def read(self, tag_name):
        try:
            return self._tags[tag_name].value
        except KeyError:
            logging.warning("Core: tagbus.read_tag(): %s tag does not exist", tag_name)

    def write(self, tag_name, value):
        if self._tags.get(tag_name, False):  # Statement executes if tag is found
            self._tags[tag_name].value = value
            #logging.info('tagbus.write_tag(): writing %s', tag_name)
        else: # Statement executes if tag is not found
            logging.warning("CORE: tagbus.write_tag(): %s tag does not exist", tag_name)

    def dump(self):
        for key, val in self.tags.items():
            logging.info('tagbus.dump(): %s %s %s', key, val.value, val.units)


class System(object):
    """System object holds all data that defines a a system process loop.
    :param self._assets: Asset objects that define physical objects in the power system
           self._modules: Dispatch process modules, either control and analytic, these modules manipulate tagbus data
           self._tagbus: Models register status and controls on the tagbus so that dispatch modules access and
                         manipulate data in a controlled way.
    """

    def __init__(self):
        self._assets = list()
        self._process = Process.ProcessContainer()
        self._tagbus = TagBus()

    @property
    def assets(self):
        return tuple(self._assets)

    @property
    def tagbus(self):
        return self._tagbus

    @property
    def process(self):
        return self._process

    def write(self, key, val):
        self._tagbus.write(key, val)

    def write_multi(self, tag_dict):
        for key, val in tag_dict.items():
            self.write(key, val)

    def read(self, key):
        return self._tagbus.read(key)

    def read_multi(self, tag_dict):
        for key in tag_dict.keys():
            tag_dict[key] = self.read(key)
        return tag_dict

    def addAsset(self, asset):
        #new_asset = dict()
        #new_asset[asset.config['name']] = asset
        self._assets.append(asset)

    def addProcess(self, new_process):
        self._process.addProcess(new_process)

    def addTagbus(self, tagbus):
        self._tagbus = tagbus

    def registerTags(self):
        """ Registers asset status and control parameters with the Tagbus

        """
        for asset in self.assets:

            for key in asset.status.keys():
                tag_name = '_'.join([asset.config['name'], key])
                self.tagbus.add(tag_name, default_value=None, units=None)

            for key in asset.config.keys():
                tag_name = '_'.join([asset.config['name'], key])
                self.tagbus.add(tag_name, default_value=None, units=None)

            for key in asset.ctrl.keys():
                tag_name = '_'.join([asset.config['name'], key])
                self.tagbus.add(tag_name, default_value=None, units=None)

        for process in self.process.process_list:
            for tag_name in process.output.keys():
                self.tagbus.add(tag_name, default_value=None, units=None)

    def updateTagbusFromAssets(self):
        """ run update_tagbus_from_asset(asset) on all assets registered in the system

        """
        for asset in self.assets:
            self.updateTagbusFromAsset(asset)

    def updateTagbusFromAsset(self, asset):
        """ Scan read parameters in asset and push that data onto the Tagbus

        :param asset: Asset object reference

        """
        for key, val in asset.status.items():
            tag_name = '_'.join([asset.config['name'], key])
            self.tagbus.write(tag_name, val)
        return

    def writeAssetsFromTagbus(self):
        """ run update_tagbus_from_asset(asset) on all assets registered in the system

        """
        for asset in self.assets:
            self.writeAssetFromTagbus(asset)

    def writeAssetFromTagbus(self, asset):
        """ Scan write parameters in asset from Tagbus data

        :param asset: Asset object reference

        """
        for key in asset.ctrl.keys():
            tag = '_'.join([asset.config['name'], key])
            asset.ctrl[key] = self.tagbus.read(tag)

    def runProcesses(self):
        """ Call run() on all processes in System._processes"""
        logging.debug('CORE: update_tagbus_from_process(): %s', self.process.process_list)
        for process in self.process.process_list:
            process.run(self)

