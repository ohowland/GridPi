#!/usr/bin/env python3

import asyncio
import logging
import unittest
from configparser import ConfigParser

from GridPi.lib.models import model_core, VirtualEnergyStorage, VirtualGridIntertie, VirtualFeeder

class TestModelModule(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

        self.parser = ConfigParser()
        self.parser.read_dict({'FEEDER':
                                   {'class_name': 'VirtualFeeder',
                                    'name': 'feeder'},
                               'ENERGY_STORAGE':
                                   {'class_name': 'VirtualEnergyStorage',
                                    'name': 'inverter'},
                               'GRID_INTERTIE':
                                   {'class_name': 'VirtualGridIntertie',
                                    'name': 'grid'}})

        self.test_asset = None
        self.loop = asyncio.get_event_loop()

    def tearDown(self):
        pass

    def test_asset_factory(self):
        logging.debug('********** Test models asset factory **********')
        asset_factory = model_core.AssetFactory()  # Create Asset Factory object

        self.test_asset = asset_factory.factory(self.parser['ENERGY_STORAGE'])
        self.assertIsInstance(self.test_asset, VirtualEnergyStorage.VirtualEnergyStorage)

        self.test_asset = asset_factory.factory(self.parser['FEEDER'])
        self.assertIsInstance(self.test_asset, VirtualFeeder.VirtualFeeder)

        self.test_asset = asset_factory.factory(self.parser['GRID_INTERTIE'])
        self.assertIsInstance(self.test_asset, VirtualGridIntertie.VirtualGridIntertie)

    def test_VES_state_machine(self):
        logging.debug('********** Test VirtualEnergyStorage state machine **********')
        asset_factory = model_core.AssetFactory()  # Create Asset Factory object
        self.test_asset = asset_factory.factory(self.parser['ENERGY_STORAGE'])
        self.loop.run_until_complete(self.test_asset.update_status())

        kw_setpoint = 50.0
        self.test_asset.control['run'] = True
        self.test_asset.control['kw_setpoint'] = kw_setpoint
        self.loop.run_until_complete(self.test_asset.update_control())
        self.loop.run_until_complete(self.test_asset.update_status())

        self.assertEqual(self.test_asset.status['online'], True)
        self.assertEqual(self.test_asset.status['kw'], kw_setpoint)

        self.test_asset.control['run'] = False
        self.loop.run_until_complete(self.test_asset.update_control())
        self.loop.run_until_complete(self.test_asset.update_status())

        self.assertEqual(self.test_asset.status['online'], False)
        self.assertEqual(self.test_asset.status['kw'], 0.0)

    def test_VES_state_machine_soc_tracking(self):
        logging.debug('********** Test VirtualEnergyStorage soc tracking **********')
        asset_factory = model_core.AssetFactory()  # Create Asset Factory object
        self.test_asset = asset_factory.factory(self.parser['ENERGY_STORAGE'])  # Virtual Energy persistence

        self.test_asset.control['run'] = True
        self.test_asset.control['kw_setpoint'] = 50.0
        self.loop.run_until_complete(self.test_asset.update_status())
        self.loop.run_until_complete(self.test_asset.update_control())

        start_soc = self.test_asset.status['soc']
        for x in range(5):
            self.loop.run_until_complete(self.test_asset.update_status())

        self.assertLess(self.test_asset.status['soc'], start_soc)

    def test_VF_state_machine(self):
        logging.debug('********** Test VirtualFeeder state machine **********')
        asset_factory = model_core.AssetFactory()  # Create Asset Factory object
        self.test_asset = asset_factory.factory(self.parser['FEEDER'])  # Virtual Feeder
        self.loop.run_until_complete(self.test_asset.update_status())

        self.test_asset.control['run'] = True
        self.loop.run_until_complete(self.test_asset.update_control())
        self.loop.run_until_complete(self.test_asset.update_status())

        self.assertEqual(self.test_asset.status['online'], True)

        self.test_asset.control['run'] = False
        self.loop.run_until_complete(self.test_asset.update_status())
        self.loop.run_until_complete(self.test_asset.update_control())

    def test_VGI_state_machine(self):
        logging.debug('********** Test VirtualGridIntertie state machine **********')

        asset_factory = model_core.AssetFactory()  # Create Asset Factory object
        self.test_asset = asset_factory.factory(self.parser['GRID_INTERTIE'])  # Virtual GridIntertie
        self.loop.run_until_complete(self.test_asset.update_status())

        self.test_asset.control['run'] = True
        self.loop.run_until_complete(self.test_asset.update_control())
        self.loop.run_until_complete(self.test_asset.update_status())

        self.assertEqual(self.test_asset.status['online'], True)

        self.test_asset.control['run'] = False
        self.loop.run_until_complete(self.test_asset.update_status())
        self.loop.run_until_complete(self.test_asset.update_control())


    def test_read_asset_container(self):
        logging.debug('********** Test read_asset_container **********')
        asset_factory = model_core.AssetFactory()  # Create Asset Factory object
        self.test_asset = asset_factory.factory(self.parser['ENERGY_STORAGE'])

        self.test_asset.status['soc'] = 0.5
        self.test_asset.config['target_soc'] = 0.6

        self.AC = model_core.AssetContainer()
        self.AC.add_asset(self.test_asset)

        search_param1 = ('inverter', 'status', 'soc')
        search_param2 = ('inverter', 'config', 'target_soc')

        resp = self.AC.read({search_param1: 0,
                             search_param2: 0})

        self.assertEqual(resp[search_param1], 0.5)
        self.assertEqual(resp[search_param2], 0.6)

if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    unittest.main()