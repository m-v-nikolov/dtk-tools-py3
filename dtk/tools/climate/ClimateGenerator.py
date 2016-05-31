import glob
import os
import time

from COMPS import Client
from COMPS.Data import QueryCriteria, AssetType
from COMPS.Data import WorkItem, WorkItemFile, WorkItem__WorkerOrPluginKey as WorkerKey
from java.util import HashMap, ArrayList

from WorkOrderGenerator import WorkOrderGenerator
from dtk.utils.ioformat.OutputMessage import OutputMessage as om


class ClimateGenerator:
    def __init__(self, demographics_file_path, work_order_path, climate_files_output_path,
                 climate_project="IDM-Zambia"):

        self.work_order_path = work_order_path
        self.demographics_file_path = demographics_file_path
        self.climate_files_output_path = climate_files_output_path
        self.climate_project = climate_project

        # see WorkOrderGenerator for other work options
        self.wo = WorkOrderGenerator(self.demographics_file_path, self.work_order_path, self.climate_project)

    def set_climate_project_info(self, climate_project):
        self.wo.set_project_info(climate_project)

    def generate_climate_files(self):
        # login to COMPS (if not already logged in) to submit climate files generation work order
        self.wo.wo_2_json()

        om("Submitting request for climate files generation to COMPS.")
        om("This requires a login.")

        # can pass setup as param and extract HPC endserver; leave hard coded for now
        Client.Login('https://comps.idmod.org')
        om("Login success!")

        workerkey = WorkerKey('InputDataWorker', '1.0.0.0_RELEASE')
        wi = WorkItem('dtk-tools InputDataWorker WorkItem', workerkey)

        tagmap = HashMap()
        tagmap.put('dtk-tools', None)
        tagmap.put('WorkItem type', 'InputDataWorker dtk-tools')
        wi.SetTags(tagmap)

        with open(self.work_order_path, 'r') as workorder_file:
            wi.AddWorkOrder(workorder_file.read())

        with open(self.demographics_file_path, 'r') as demog_file:
            wi.AddFile(WorkItemFile(os.path.basename(self.demographics_file_path), 'Demographics', ''),
                       demog_file.read())

        wi.Save()

        om("Created request for climate files generation.")
        om("Commissioning...")

        wi.Commission()

        while (wi.getState().toString() not in ['Succeeded', 'Failed', 'Canceled']):
            om('Waiting for climate generation to complete (current state: ' + wi.getState().toString() + ')',
               style='flushed')
            time.sleep(0.1)
            wi.Refresh()

        om("Climate files SUCCESSFULLY generated")

        wi.Refresh(QueryCriteria().SelectChildren('Files'))
        wifiles = wi.getFiles().toArray()

        wifilenames = [wif.getFileName() for wif in wifiles if wif.getFileType() == 'Output']
        if len(wifilenames) > 0:
            om('Found output files: ' + str(wifilenames))
            om('Downloading now')

            javalist = ArrayList()
            for f in wifilenames:
                javalist.add(f)

            assets = wi.RetrieveAssets(AssetType.Linked, javalist)

            for i in range(len(wifilenames)):
                om('Writing ' + wifilenames[i] + ' to ' + self.climate_files_output_path)

                with open(os.path.join(self.climate_files_output_path, wifilenames[i]), 'wb') as outfile:
                    outfile.write(assets.get(i).tostring())

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
