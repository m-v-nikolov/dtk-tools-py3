import glob
import json
import os
import time
import zipfile
from dtk.utils.ioformat.OutputMessage import OutputMessage as om
from simtools.COMPSAccess.InputDataWorker import InputDataWorker
from simtools.SetupParser import SetupParser
from simtools.Utilities.General import file_size


class ClimateGenerator:
    def __init__(self, demographics_file_path, work_order_path, climate_files_output_path,
                 climate_project="IDM-Zambia", start_year=2000, num_years=1, resolution=0, idRef=None):

        self.work_order_path = work_order_path
        self.demographics_file_path = demographics_file_path
        self.climate_project = climate_project
        self.start_year = start_year
        self.num_years = num_years
        self.resolution = resolution
        self.wo = None

        # Get the idRef from the demographics_file if notspecified
        demog = json.load(open(demographics_file_path, 'r'))
        demog_idref = demog['Metadata']['IdReference']
        if not idRef:
            self.idRef = demog_idref
        else:
            self.idRef = idRef
            if idRef != demog_idref:
                print("/!\\ Warning: the idref of the demographics file ({}) "
                      "is different from the one passed ({})".format(demog_idref, idRef))

        self.climate_files_output_path = climate_files_output_path
        if not os.path.exists(self.climate_files_output_path): os.makedirs(self.climate_files_output_path)

    def generate_climate_files(self):
        # see InputDataWorker for other work options
        self.wo = InputDataWorker(demographics_file_path=self.demographics_file_path,
                                  wo_output_path=self.work_order_path,
                                  project_info=self.climate_project,
                                  start_year=self.start_year,
                                  num_years=self.num_years,
                                  resolution=self.resolution,
                                  idRef=self.idRef)

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

        print("Created request for climate files generation.")
        print("Commissioning...")

        wi.commission()

        while wi.state not in (WorkItemState.Succeeded, WorkItemState.Failed, WorkItemState.Canceled):
            om('Waiting for climate generation to complete (current state: ' + str(wi.state) + ')',  style='flushed')
            time.sleep(5)
            wi.refresh()

        print("Climate files SUCCESSFULLY generated")

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

            print('Climate files SUCCESSFULLY stored.')

            return rain_file_name, temperature_file_name, humidity_file_name

        else:
            print('No output files found')