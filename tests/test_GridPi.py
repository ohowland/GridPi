import unittest
import logging
import asyncio
import time

from GridPi import Core
from Models import Models
from Process import Process
from Persistence import Persistence
from configparser import ConfigParser

import unittest

class TestGridPi(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)  # configure logging
        self.gp = Core.System()

        # configure asset models
        parser = ConfigParser()
        parser.read_dict({'FEEDER':
                                   {'class_name': 'VirtualFeeder',
                                    'name': 'feeder'},
                               'ENERGY_STORAGE':
                                   {'class_name': 'VirtualEnergyStorage',
                                    'name': 'inverter'},
                               'GRID_INTERTIE':
                                   {'class_name': 'VirtualGridIntertie',
                                    'name': 'grid'}})

        asset_factory = Models.AssetFactory()  # Create Asset Factory object
        for cfg in parser.sections():  # Add Models to System, The asset factory acts on a configuration
            self.gp.add_asset(asset_factory.factory(parser[cfg]))
        del asset_factory

        # configure processes
        parser.clear()
        parser.read_dict({'process_1': {'class_name': 'INV_UPT_STATUS'},
                               'process_2': {'class_name': 'GRID_UPT_STATUS'},
                               'process_3': {'class_name': 'INV_SOC_PWR_CTRL',
                                             'inverter_target_soc': 0.6},
                               'process_4': {'class_name': 'INV_DMDLMT_PWR_CTRL',
                                             'grid_kw_import_limit': 20,
                                             'grid_kw_export_limit': 20},
                               'process_5': {'class_name': 'INV_WRT_CTRL'}})
        process_factory = Process.ProcessFactory()
        for cfg in parser.sections():
            self.gp.add_process(process_factory.factory(parser[cfg]))
        del process_factory

        parser.clear()
        parser.read_dict({'PERSISTENCE':
                              {'class_name': 'DBSQLite3',
                               'local_path': '/database/GridPi.sqlite',
                               'empty_database_on_start': 1}})
        persistence_factory = Persistence.PersistenceFactory()
        for cfg in parser.sections():
            self.db = persistence_factory.factory(parser[cfg])
        del persistence_factory

        self.gp.register_tags() # System will register all Asset object parameters
        self.gp.process.sort(self.gp)

    def test_async_asset_update(self):
        loop_update = asyncio.get_event_loop()
        for x in range(3):
            # Collect updateStatus() method references for each asset and package as coroutine task.
            tasks = asyncio.gather(*[x.updateStatus() for x in self.gp.assets.values()])
            loop_update.run_until_complete(tasks)

    def test_async_asset_write(self):
        loop_write = asyncio.get_event_loop()
        for x in range(3):
            # Collect updateStatus() method references for each asset and package as coroutine task.
            tasks = asyncio.gather(*[x.updateCtrl() for x in self.gp.assets.values()])
            loop_write.run_until_complete(tasks)

if __name__ == '__main__':
    unittest.main()