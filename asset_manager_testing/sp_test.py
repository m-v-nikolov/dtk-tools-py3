from simtools.SetupParser import SetupParser

SetupParser.init(selected_block='AM')

print "base_collection_id_dll : %s" % SetupParser.get('base_collection_id_dll')
