from dtk.utils.parsers.JSON import json2dict

class Template(object):

    def __init__(self, filename, template_type, use_KP = False):
        self.filename = filename

        # The template "prefix" is the keyword used to determine
        # which file contains the parameter to edit.  Possible 
        # options for prefix include CONFIG, CAMPAIGN, and TEMPLATE
        # These files are described in the plugin_files.json file by
        # as the prefix concatenated with _TEMPLATE, e.g. CONFIG_TEMPLATE.
        # Here, we remove the _TEMPLATE:
        self.template_prefix = template_type.replace("_TEMPLATE","")
        self.use_KP = use_KP

        if self.use_KP:
            self.updater = self.update_KP_param
        else:
            self.updater = self.update_config_param

        self.data = json2dict(filename)

    @classmethod
    def as_config(cls, filename, template_type):
        return cls(filename, template_type, False)

    @classmethod
    def as_KP(cls, filename, template_type):
        return cls(filename, template_type, True)

    def update_param(self, param, value):
        self.updater(param, value)

    def update_params(self, params):
        if self.template_prefix not in params:
            print "NO SOUP FOR",self.filename, self.template_prefix, params.keys()
            return
        my_params = params[self.template_prefix]

        for k,v in my_params.items():
            self.update_param(k,v)

    def update_config_param(self, param, value):
        print "Setting",param,"=",value,"in",self.filename
        cleaned_param = param
        if "CONFIG" in param:
            print "CLEANING CONFIG."
            # e.g. CONFIG.Vector_Species_Params.arabiensis.Acquire_Modifier
            # Removes the CONFIG. part
            cleaned_param = param.replace("CONFIG.","")

        self.data[cleaned_param] = value
        print "NEW DATA",self.data

        return {param:value}


    def update_KP_param(self, param, value):
        print "TODO: Set KP parameter in file %s" % self.filename

