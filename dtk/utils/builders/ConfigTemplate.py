import dtk.utils.builders.ITemplate as ITemplate

class ConfigTemplate(ITemplate.BaseTemplate):
    '''
    A class for building, modifying, and writing config.json DTK input files.
    '''

    def __init__(self, filename, contents):
        '''
        Initialize a ConfigTemplate.
        :param filename: The name of the template file.  This is not the full path to the file, just the filename.
        :param contents: The contents of the template file
        '''

        super(ConfigTemplate, self).__init__(filename, contents)

        self.contents = self.contents['parameters'] # Remove "parameters"
        ###self.known_params = {}


    # ITemplate functions follow
    def get_contents(self):
        '''
        Get contents, restoring "parameters"
        :return: The potentially modified contents of the template file
        '''
        return {"parameters": self.contents}

    """
    def has_param(self, param):
        '''
        Boolean to determine if this template can set param.
        :return: Boolean
        '''
        if param in self.known_params:
            return self.known_params[param]

        # First time looking for this parameter.  Try to find it and add to list of known parameters
        try:
            value = self.get_param(param)
            is_param = True
        except (KeyError, TypeError, IndexError) as e:
            is_param = False

        self.known_params[param] = is_param
        return is_param
    """

    def set_params_and_modify_cb(self, params, cb):
        '''
        Set parameters and modify a DTKConfigBuilder
        :param params: Dictionary of params
        :param cb: DTKConfigBuilder 
        :return: Dictionary of tags
        '''
        tags = self.set_params(params)
        cb.config = self.get_contents()
        return tags

