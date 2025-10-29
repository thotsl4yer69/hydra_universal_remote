import importlib, traceback, sys
print('PYTHON', sys.version)
try:
    m = importlib.import_module('bleak')
    print('bleak module:', m)
    from bleak import BleakScanner
    print('BleakScanner:', BleakScanner)
except Exception:
    print('Import failed:')
    traceback.print_exc()
