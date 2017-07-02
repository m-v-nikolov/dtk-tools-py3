import glob
import os
import time
import zipfile
from dtk.utils.ioformat.OutputMessage import OutputMessage as om
from simtools.COMPSAccess.InputDataWorker import InputDataWorker
from simtools.SetupParser import SetupParser
from simtools.Utilities.General import file_size


class ClimateGenerator:
    def __init__(self, demographics_file_path, work_order_path, climate_files_output_path,
                 climate_project="IDM-Zambia"):

        self.work_order_path = work_order_path
        self.demographics_file_path = demographics_file_path
        self.climate_files_output_path = climate_files_output_path
        if not os.path.exists(self.climate_files_output_path): os.makedirs(self.climate_files_output_path)
        self.climate_project = climate_project

        # see InputDataWorker for other work options
        self.wo = InputDataWorker(self.demographics_file_path, self.work_order_path, self.climate_project,
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

        from COMPS.Data.WorkItem import WorkerOrPluginKey, WorkItemState
        from COMPS.Data import QueryCriteria
        from COMPS.Data import WorkItem, WorkItemFile
        from COMPS.Data import AssetCollection

        workerkey = WorkerOrPluginKey(name='InputDataWorker', version='1.0.0.0_RELEASE')
        wi = WorkItem('dtk-tools InputDataWorker WorkItem', workerkey, SetupParser.get('environment'))
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

        while wi.state not in (WorkItemState.Succeeded, WorkItemState.Failed, WorkItemState.Canceled):
            om('Waiting for climate generation to complete (current state: ' + str(wi.state) + ')',
               style='flushed')
            time.sleep(5)
            wi.refresh()

        om("Climate files SUCCESSFULLY generated")

        # Get the collection with our files
        collections = wi.get_related_asset_collections()
        collection_id = collections[0].id
        comps_collection = AssetCollection.get(collection_id, query_criteria=QueryCriteria().select_children('assets'))

        # Get the files
        if len(comps_collection.assets) > 0:
            print("Found output files:")
            for asset in comps_collection.assets:
                print("- %s (%s)" % (asset.file_name, file_size(asset.length)))

            print("\nDownloading to %s..." % self.climate_files_output_path)

            # Download the collection as zip
            zip_path = os.path.join(self.climate_files_output_path, 'temp.zip')
            with open(zip_path, 'wb') as outfile:
                outfile.write(comps_collection.retrieve_as_zip())

            # Extract it
            zip_ref = zipfile.ZipFile(zip_path, 'r')
            zip_ref.extractall(self.climate_files_output_path)
            zip_ref.close()

            # Delete the temporary zip
            os.remove(zip_path)

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