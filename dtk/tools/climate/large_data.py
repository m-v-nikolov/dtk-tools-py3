import glob
import os
import shutil
import json
import subprocess
import sys

"""
This dump_climate_files function is intended
to be staged on the machine that hosts the large data tools
(currently app07, E:\LDTools)
to combine data in intermediate files dumped by climate processing algorithms
to output DTK-consumable input files.
"""

LDTools_path = 'E:/LDTools/Release'
tmp_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'tmp')

def dump_climate_files( geography  = "EMOD-Zambia",
                        resolution = 150,
                        tag        = "_test_",
                        nodelist   = []):

    # Read, modify, and dump local copy of JSON instructions
    # Expose other options directly, e.g. year range?
    with open(os.path.join(LDTools_path,'MergeNodeJson.json'),'r') as mnjf:
        mnj = json.loads(mnjf.read())

    mnj['startyear'] = 2001
    mnj['numyears']  = 11
    mnj['author']    = 'Institute for Disease Modeling'
    mnj['tag']       = tag
    if nodelist:
        mnj['usenodelist'] = True
        mnj['nodelist']    = nodelist
    print(mnj)

    if not os.path.exists(tmp_path):
        os.makedirs(tmp_path)
    
    with open( os.path.join( tmp_path, "mnj.json"), "w" ) as mnjf:
        mnjf.write( json.dumps( mnj, sort_keys=True, indent=2 ) )

    # Construct three function calls:
    # tmean, humid, rain (--yislat on rain)
    for mn_param in ['tmean','humid','rain']:
        mn_args = [os.path.join(LDTools_path,'MergeNodes.exe'),
                         '-j' + os.path.join(tmp_path, 'mnj.json'),
                         '-p' + mn_param]
        if 'rain' in mn_param:
            print(mn_param)
            mn_args.append('--yislat')

        mn_args.extend(['-r' + str(resolution), geography])
        print(mn_args)
        subprocess.call(mn_args)

'''
Two more helper functions to copy climate and demographics files from where they are dumped
by Dennis' scripts and put them into the SVN repository directory for check-in.

Some clean-up and validation done on the fly.
'''

def copy_demog(geography, resolution, tag, source, target):
    
    # Demographics
    demogfiles = glob.glob(source + '/*.json') # refine by tag?
    for file in demogfiles:
        if not 'compiled' in file:
            demogfile = file
            break

    # Finally the demographics file
    with open( demogfile, "r" ) as json_file:
        demog = json.loads( json_file.read() )

    # Fix malformed bits
    if "BirthRate" in demog["Defaults"]["IndividualAttributes"]:
        del demog["Defaults"]["IndividualAttributes"]["BirthRate"]
    for node in demog["Nodes"]:
        na=node["NodeAttributes"]
        if "AbovePoverety" in na:
            na["AbovePoverty"] = na.pop("AbovePoverety")
        na["AbovePoverty"] = 0.5 # NodeDemographics complains if it is NULL
        if "NodeId" in node:
            node["NodeID"] = node.pop("NodeId")

    import collections
    nodelist = [node["NodeID"] for node in demog["Nodes"]]
    #for x,y in collections.Counter(nodelist).items():
    #    print("Node id %d has %d entries" % (x,y))
    print("There are %d nodes" % len(nodelist))
    print("There are %d unique nodes" % len(collections.Counter(nodelist)))

    demog_output = target + "/" + geography + "_" + resolution + "_demographics.json"
    output_file = open( demog_output, "w" )
    output_file.write( json.dumps( demog, sort_keys=True, indent=4 ) )
    output_file.close()

    # Compile the demographics file (forcing overwrite)
    subprocess.call([sys.executable, 'compiledemog.py', demog_output, "--forceoverwrite"])

def copy_climate(geography, resolution, tag, source, target):

    wildcard = '*'
    if tag:
        wildcard += tag + '*'

    # Get most recent rainfall binary file and JSON header
    rainfile = max(glob.glob(source + '/rain/' + wildcard + '.bin'), key=os.path.getctime)
    rainfileheader = max(glob.glob(source + '/rain/' + wildcard + '.json'), key=os.path.getctime)
    print("Copying " + rainfile)

    # Get most recent humidity binary file and JSON header
    humidfile = max(glob.glob(source + '/humid/' + wildcard + '.bin'), key=os.path.getctime)
    humidfileheader = max(glob.glob(source + '/humid/' + wildcard + '.json'), key=os.path.getctime)
    print("Copying " + humidfile)

    # Get most recent air temperature binary file and JSON header
    airtempfile = max(glob.glob(source + '/tmean/' + wildcard + '.bin'), key=os.path.getctime)
    airtempfileheader = max(glob.glob(source + '/tmean/' + wildcard + '.json'), key=os.path.getctime)
    print("Copying " + airtempfile)

    # Copy newly generated files to target SVN directory
    shutil.copyfile(rainfile, target + "/" + geography + "_" + resolution + "_rainfall_daily.bin")
    shutil.copyfile(rainfileheader, target + "/" + geography + "_" + resolution + "_rainfall_daily.bin.json")
    shutil.copyfile(humidfile, target + "/" + geography + "_" + resolution + "_relative_humidity_daily.bin")
    shutil.copyfile(humidfileheader, target + "/" + geography + "_" + resolution + "_relative_humidity_daily.bin.json")
    shutil.copyfile(airtempfile, target + "/" + geography + "_" + resolution + "_air_temperature_daily.bin")
    shutil.copyfile(airtempfileheader, target + "/" + geography + "_" + resolution + "_air_temperature_daily.bin.json")

    # For the time being, use air-temperature also for land-temperature (unused by DTK)
    shutil.copyfile(airtempfile, target + "/" + geography + "_" + resolution + "_land_temperature_daily.bin")

    # Put a note of this into land-temperature meta-data
    json_file = open( airtempfileheader, "r" )
    header = json.loads( json_file.read() )
    header["Metadata"]["DataProvenance"] = "Temporarily just a copy of air-temperature for " + geography + " - currently unused by the DTK"
    json_file.close()
    output_file = open( target + "/" + geography + "_" + resolution + "_land_temperature_daily.bin.json", "w" )
    output_file.write( json.dumps( header, sort_keys=True, indent=4 ) )
    output_file.close()

if __name__ == "__main__":

    geography  = "Zambia"      #  "Zambia" "Mozambique_Zambezia" "Kenya_Nyanza"
    resolution = "30arcsec"   #  "2_5arcmin" "30arcsec"
    tag        = "Gwembe_Sinazongwe"  #  "Sinamalima", "Manhica"

    sourcedir = "IDM-" + geography
    source_res = '2.5m' if resolution == '2_5arcmin' else '30s'
    source = "//rivendell/archive/LargeData/Data/Out/" + sourcedir + "/" + geography + "/DTK_" + source_res
    target = "D:/Eradication/Data_Files/" + geography
    if tag:
        target = os.path.join(target,tag)
        geography = '_'.join([geography,tag])

    # Create output directory if it doesn't yet exist
    if not os.path.exists(target):
        os.makedirs(target)

    #dump_climate_files('EMOD-Zambia', 150, '_Sinamalima_',[326436567])
    '''
    dump_climate_files('EMOD-Zambia',30,'_Gwembe_Sinazongwe_',
                        [1631855153, 1631920687, 1631920699, 1632117293, 1632117296, 1632182850, 1632248369, 1632248372, 1632313919, 1632379437,
                         1632444978, 1632444980, 1632510528, 1632510541, 1632576053, 1632641588, 1632641605, 1632641652, 1632641654, 1632707121,
                         1632707187, 1632707190, 1632838197, 1632838207, 1632903735, 1632969274, 1632969285, 1633034804, 1633034832, 1633034866,
                         1633100344, 1633100347, 1633165886, 1633165892, 1633165895, 1633231420, 1633296952, 1633296973, 1633297001, 1633297009,
                         1633362483, 1633428027, 1633493589, 1633559139, 1633559152, 1633690179, 1633690217, 1633821260, 1633821266, 1633821275,
                         1633821294, 1633886826, 1633886836, 1633952356, 1634017870, 1634017900, 1634083413, 1634214499, 1634280040, 1634280046,
                         1634411088, 1634411092, 1634411128, 1634476625, 1634542162, 1634607697, 1634607730, 1634673230, 1634673232, 1634738769,
                         1634738789, 1634738794, 1634804308, 1634804312, 1634935380, 1634935411, 1635000916, 1635000937, 1635000942, 1635066454,
                         1635132018, 1635197534, 1635328598, 1635328637, 1635394129, 1635394160, 1635394164, 1635590773, 1635656297, 1635656312,
                         1635721820, 1635721845, 1635852918, 1635918443, 1636115064, 1636180565, 1636180575, 1636180600, 1636246136, 1636311653,
                         1636311660, 1636311668, 1636442738, 1636508279, 1636639321, 1636639348, 1636639354, 1636704880, 1636770422, 1636835938,
                         1636835963, 1637032573, 1637360229, 1637360242, 1637556842, 1637950058])
    '''

    copy_climate(geography, resolution, tag, source, target)
    #copy_demog(geography, resolution, tag, source, target)