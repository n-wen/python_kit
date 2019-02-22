import sys
PYTHON3 = True if sys.version_info[0] == 3 else False
if PYTHON3:
    from .app import PythonKit, Servicer
else:
    from .app_v2 import PythonKit, Servicer
