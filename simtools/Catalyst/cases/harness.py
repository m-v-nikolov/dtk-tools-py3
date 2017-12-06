import json
import os
from subprocess import call

debug = False

root_dir = os.path.abspath(os.path.dirname(__file__))
command_root = ['dtk', 'catalyst']

configs = json.load(open('cases.json', mode='r'))

for config in configs:
    print(config)
    if config.get('run', 'True') == 'False':
        print('Skipping above configuration...')
        continue

    if config['directory'] is '':
        continue
    working_dir = os.path.abspath(config['directory'])
    os.chdir(working_dir)
    print('\n--------------------------------\ncd: %s' % working_dir)
    args = [arg for arg in command_root + config['args'].split(' ') if arg is not '']
    print('Calling: %s' % args)
    if not debug:
        call(args)
    os.chdir(root_dir)