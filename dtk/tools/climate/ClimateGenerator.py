import glob
import os
import time
from collections import namedtuple

from dtk.utils.ioformat.OutputMessage import OutputMessage as om
from simtools.COMPSAccess.WorkOrderGenerator import WorkOrderGenerator
from simtools.Utilities.COMPSUtilities import COMPS_login
from simtools.SetupParser import SetupParser


class ClimateGenerator:
    def __init__(self, demographics_file_path, work_order_path, climate_files_output_path, setup,
                 climate_project="IDM-Zambia"):

        self.setup = setup
        self.work_order_path = work_order_path
        self.demographics_file_path = demographics_file_path
        self.climate_files_output_path = climate_files_output_path
        self.climate_project = climate_project

        # see WorkOrderGenerator for other work options
        self.wo = WorkOrderGenerator(self.demographics_file_path, self.work_order_path, self.climate_project,
                                     idRef='Gridded world grump30arcsec')

    def set_climate_project_info(self, climate_project):
        self.wo.set_project_info(climate_project)

    def set_climate_start_year(self, start_year):
        self.wo.set_start_year(start_year)

    def set_climate_num_years(self, num_years):
        self.wo.set_num_years(num_years)

    def set_climate_id_ref(self, id_ref):
        self.wo.set_id_ref(id_ref)

    def generate_climate_files(self):
        # login to COMPS (if not already logged in) to submit climate files generation work order
        self.wo.wo_2_json()

        om("Submitting request for climate files generation to COMPS.")
        om("This requires a login.")

        from COMPS.Data.WorkItem import WorkerOrPluginKey, WorkItemState
        from COMPS.Data import QueryCriteria, AssetType
        from COMPS.Data import WorkItem, WorkItemFile

        # COMPS_login(self.setup.get('server_endpoint'))
        sp = SetupParser('HPC', force=True)
        om("Login success!")

        workerkey = WorkerOrPluginKey(name='InputDataWorker', version='1.0.0.0_RELEASE')
        wi = WorkItem('dtk-tools InputDataWorker WorkItem', workerkey, sp.get('environment'))
        wi.set_tags({'dtk-tools': None, 'WorkItem type': 'InputDataWorker dtk-tools'})

        with open(self.work_order_path, 'r') as workorder_file:
            # wi.AddWorkOrder(workorder_file.read())
            wi.add_work_order(data=workorder_file.read())

        with open(self.demographics_file_path, 'r') as demog_file:
            wi.add_file(WorkItemFile(os.path.basename(self.demographics_file_path), 'Demographics', ''),
                        data=demog_file.read())

        wi.save()

        om("Created request for climate files generation.")
        om("Commissioning...")

        wi.commission()

        while (wi.state not in [WorkItemState.Succeeded, WorkItemState.Failed, WorkItemState.Canceled]):
            om('Waiting for climate generation to complete (current state: ' + str(wi.state) + ')',
               style='flushed')
            time.sleep(0.1)
            wi.refresh()

        om("Climate files SUCCESSFULLY generated")

        wi.refresh(QueryCriteria().select_children('files'))
        wifilenames = [wif.file_name for wif in wi.files if wif.file_type == 'Output']

        # wifilenames = [wif.file_name() for wif in wifiles if wif.file_type() == 'Output']
        if len(wifilenames) > 0:
            om('Found output files: ' + str(wifilenames))
            om('Downloading now')

            assets = wi.retrieve_assets(AssetType.Linked, wifilenames)

            for i in range(len(wifilenames)):
                om('Writing ' + wifilenames[i] + ' to ' + self.climate_files_output_path)

                with open(os.path.join(self.climate_files_output_path, wifilenames[i]), 'wb') as outfile:
                    outfile.write(assets[i])

            # return filenames; this use of re in conjunction w/ glob is not great; consider refactor
            rain_bin_re = os.path.abspath(self.climate_files_output_path + '/*rain*.bin')
            humidity_bin_re = os.path.abspath(self.climate_files_output_path + '/*humidity*.bin')
            temperature_bin_re = os.path.abspath(self.climate_files_output_path + '/*temperature*.bin')

            rain_file_name = os.path.basename(glob.glob(rain_bin_re)[0])
            humidity_file_name = os.path.basename(glob.glob(humidity_bin_re)[0])
            temperature_file_name = os.path.basename(glob.glob(temperature_bin_re)[0])

            om('Climate files SUCCESSFULLY stored.')

            return {'rain': rain_file_name, 'temp': temperature_file_name, 'humidity': humidity_file_name}

        else:
            om('No output files found')