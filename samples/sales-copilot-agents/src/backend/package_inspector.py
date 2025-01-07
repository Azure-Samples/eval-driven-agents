import pkgutil
import importlib
import azure.ai.projects as projects
import azure.ai.inference as inference

def inspect_package(package, name):
    print(f'\n{name} modules:')
    for module in pkgutil.iter_modules(package.__path__):
        print(f'- {module.name}')
        try:
            submodule = importlib.import_module(f'{package.__name__}.{module.name}')
            print('  Contents:')
            for item in dir(submodule):
                if not item.startswith('__'):
                    print(f'    - {item}')
        except ImportError as e:
            print(f'  Error importing {module.name}: {e}')

print('Inspecting Azure AI packages...')
inspect_package(projects, 'Azure AI Projects')
inspect_package(inference, 'Azure AI Inference')
