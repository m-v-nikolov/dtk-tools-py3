import dtk.utils.builders.BaseTemplate as BaseTemplate

class ConfigTemplate(BaseTemplate.BaseTemplate):
    """
    A class for building, modifying, and writing config.json DTK input files.
    """

    def __init__(self, filename, contents):
        """
        Initialize a ConfigTemplate.
        :param filename: The name of the template file.  This is not the full path to the file, just the filename.
        :param contents: The contents of the template file
        """

        super(ConfigTemplate, self).__init__(filename, contents)

        self.contents = self.contents['parameters'] # Remove "parameters"


    # ITemplate functions follow
    def get_contents(self):
        """
        Get contents, restoring "parameters"
        :return: The potentially modified contents of the template file
        """
        return {"parameters": self.contents}


    def set_params_and_modify_cb(self, params, cb):
        """
        Set parameters and modify a DTKConfigBuilder
        :param params: Dictionary of params
        :param cb: DTKConfigBuilder 
        :return: Dictionary of tags
        """
        tags = self.set_params(params)
        cb.config = self.get_contents()
        return tags

