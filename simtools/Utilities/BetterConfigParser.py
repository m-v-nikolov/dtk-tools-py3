from configparser import SafeConfigParser, DEFAULTSECT


class BetterConfigParser(SafeConfigParser):
    """
    This ConfigParser provides a bypass_defaults flag in the has_option method to be able to check
    the config and ignore the eventual DEFAULT block.
    """
    def has_option(self, section, option, bypass_defaults=False):
        """Check for the existence of a given option in a given section."""
        if not section or section == DEFAULTSECT:
            option = self.optionxform(option)
            return option in self._defaults
        elif section not in self._sections:
            return False
        else:
            option = self.optionxform(option)
            return (option in self._sections[section]
                    or (option in self._defaults and not bypass_defaults))

    def items(self, *args, **kwargs):
        """
        Identical to superclass .items, except that keys that are included only due to application of default values
        can be excluded from the list.
        :param exclude_default_value_items: If True, exclude options only present due to default value application.
        :param kwargs: args for super()
        :return: a list of items, as per super modified by the above
        """
        exclude_default_value_items = kwargs.pop('exclude_default_value_items', False)
        section = kwargs.get('section') if kwargs.get('section', None) else args[0]
        all_items = super(BetterConfigParser, self).items(*args, **kwargs)
        if exclude_default_value_items:
            return_items = [(opt,value) for (opt,value) in all_items
                            if self.has_option(section=section, option=opt, bypass_defaults=True)]
        else:
            return_items = all_items
        return return_items
