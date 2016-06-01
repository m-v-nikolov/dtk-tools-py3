import abc

class ITemplate(object):
    __metaclass__  = abc.ABCMeta

    @abc.abstractmethod
    def get_filename(self):
        """
        Gets the file name.
        :return: The filename
        """

    @abc.abstractmethod
    def get_contents(self):
        """
        Returns the file contents, potentially modified.
        :return: file contents
        """

    @abc.abstractmethod
    def is_consumed_by_template(self, parameter):
        """Checks if key is used by the template
        :param key: The key to look for
        :return: Boolean.
        """

    @abc.abstractmethod
    def set_params(self, param_dict):
        """
        Sets parameters.
        :param param_dict: A dictionary of key value pairs to set.  Keys not used by the template will be ignored.
        :return: tag dictionary of key value pairs that were set.
        """

    @abc.abstractmethod
    def get_param(self, param):
        """
        Gets a parameter value.  The return type is a dictionary because some tagged parameters can have multiple addresses, and therefore multiple values.
        :param param: The parameter, may contain '.' and numeric indices, '[0]',  e.g. Events[3].Start_Day
        :return: A dictionary of key value pairs
        """

    def set_params_and_modify_cb(self, params, cb):
        """
        Sets parameters and potentially also modifies a config builder instance
        :param params: A dictionary of parameters to set
        :param cb: An instance of a DTKConfigBuilder
        :return: Simulation tags
        """


class BaseTemplate(ITemplate):
    def get_param(self, param):
        path_steps = param.split('.')

        current_parameter = self.contents

        for path_step in path_steps:
            if '[' in path_step:
                subpaths = path_step.split('[')
                assert( subpaths[1][-1] == ']' )
                path_step = subpaths[0]
                index = int(float(subpaths[1][:-1]))
                current_parameter = current_parameter[self.cast_value(path_step)]
                current_parameter = current_parameter[index]
            else:
                # If the step is a number, we are in a list, we need to cast the step to int
                current_parameter = current_parameter[self.cast_value(path_step)]

        return {param: current_parameter}


    def cast_value(self,value):
        """
        Try to cas a value to float or int or string
        :param value:
        :return:
        """
        # The value is already casted
        if not isinstance(value, str) and not isinstance(value, unicode):
            return value

        # We have a string so test if only digit
        if value.isdigit():
            casted_value =  int(value)
        else:
            try:
                casted_value = float(value)
            except:
                casted_value = value

        return casted_value
    


