from ConfigParser import SafeConfigParser, DEFAULTSECT


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
