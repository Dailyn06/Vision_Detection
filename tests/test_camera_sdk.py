import ctypes
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from vision.camera.controller import find_sdk_directory, MindVisionCamera


class SDKDiscoveryTests(unittest.TestCase):
    def test_vendor_installation_matches_python_architecture(self):
        with TemporaryDirectory() as directory:
            sdk = Path(directory) / 'MindVision' / 'SDK'
            is_64bit = ctypes.sizeof(ctypes.c_void_p) == 8
            if is_64bit:
                sdk /= 'X64'
            sdk.mkdir(parents=True)
            (sdk / ('MVCAMSDK_X64.dll' if is_64bit else 'MVCAMSDK.dll')).touch()
            with patch.dict(os.environ, {'ProgramFiles(x86)': directory, 'ProgramFiles': directory}):
                self.assertEqual(find_sdk_directory(), sdk)
                self.assertEqual(find_sdk_directory(directory), Path(directory).resolve())

    def test_ctypes_missing_dll_error_has_actionable_message(self):
        with patch('vision.camera.controller.platform.system', return_value='Windows'), \
             patch('vision.camera.controller.find_sdk_directory', return_value=None), \
             patch('vision.camera.controller.importlib.import_module', side_effect=AttributeError('MVCAMSDK_X64')):
            with self.assertRaisesRegex(RuntimeError, 'specify --sdk-dir'):
                MindVisionCamera().__enter__()


if __name__ == '__main__':
    unittest.main()
