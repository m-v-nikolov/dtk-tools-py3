import os
import logging
import logging.config

logging_initialized = False

# print('--- enter __init-- --')
# current_dir = os.path.dirname(os.path.realpath(__file__))
# config_file = os.path.join(current_dir, 'logging.ini')
# print('config_file: %s' % config_file)
# print('config_file: %s' % os.path.exists(config_file))
# logging.config.fileConfig(os.path.join(current_dir, 'logging.ini'), disable_existing_loggers=False)
# print(logging.config)
# print(logging)


# logging_file = r'H:\temp\example.log'
# logging.basicConfig(filename=logging_file)

# __all__ = ['my_logging']

def get_logging():
    global logging_initialized

    if not logging_initialized:
        current_dir = os.path.dirname(os.path.realpath(__file__))
        # config_file = os.path.join(current_dir, 'logging.ini')
        # print('config_file: %s' % config_file)
        # print('config_file: %s' % os.path.exists(config_file))
        logging.config.fileConfig(os.path.join(current_dir, 'logging.ini'), disable_existing_loggers=False)
        # print(logging)

    return logging
