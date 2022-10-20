import os
import unittest

#from . import archive

#scripts_dir = archive.copy_from_container(container, context.irods_home())
#logging.info(f'downloaded scripts to [{scripts_dir}]')

loader = unittest.TestLoader()
#suite = loader.discover(os.path.join(scripts_dir, 'scripts'), pattern='test_*.py')
#discovery = loader.discover(os.path.join(scripts_dir, 'irods/scripts'), pattern='test_*.py')
discovery = loader.discover('/var/lib/irods/scripts', pattern='test_*.py')
tests = list()
for m in discovery:
    #print(f'found module: [{m}]')
    for s in m._tests:
        #print(f'found suite: [{s}]')
        try:
            for t in s._tests:
                #print(f'found test: [{t}]')
                module = t.__module__
                cls = t.__class__.__name__
                test = t._testMethodName
                t = '.'.join([module, cls, test])
                #print('.'.join(t.split('.')[2:]))
                tests.append('.'.join(t.split('.')[2:]))

        except AttributeError:
            continue

#print('>>> test list here <<<')
#print(tests)
#print('>>> test list done <<<')

for t in tests:
    print(t)
