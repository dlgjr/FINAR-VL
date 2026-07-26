import os, sys, struct
import ctypes
import ctypes.util
from functools import wraps
from typing import Callable, TypeVar
import logging

logger = logging.getLogger(__name__)
LibCall = TypeVar("LibCall")

def lookup_dll(prefix):
    paths = os.environ.get("PATH", "").split(os.pathsep)
    for path in paths:
        if not os.path.exists(path):
            continue
        for name in os.listdir(path):
            if name.startswith(prefix) and name.lower().endswith(".dll"):
                return os.path.join(path, name)
    return None

def unix_find_lib(name):
    cuda_path = os.environ.get("CUDA_PATH", None)
    if cuda_path is not None:
        lib_name = os.path.join(cuda_path, "lib64", "lib%s.so" % name)
        if os.path.exists(lib_name):
            return lib_name

    cuda_path = "/usr/local/cuda"
    if cuda_path is not None:
        lib_name = os.path.join(cuda_path, "lib64", "lib%s.so" % name)
        if os.path.exists(lib_name):
            return lib_name

    lib_name = ctypes.util.find_library(name)
    return lib_name

def windows_find_lib(name):
    lib_name = "%s%d_" % (name, struct.calcsize("P") * 8)
    return lookup_dll(lib_name)

class Lib:
    def __init__(self, name):
        self.__name = name
        if sys.platform.startswith("win"):
            lib_path = windows_find_lib(self.__name)
            self.__lib_path = lib_path
            if lib_path is not None:
                self.__lib = ctypes.WinDLL(lib_path)
            else:
                self.__lib = None
        elif sys.platform.startswith("linux"):
            lib_path = unix_find_lib(self.__name)
            self.__lib_path = lib_path
            if lib_path is not None:
                self.__lib = ctypes.cdll.LoadLibrary(lib_path)
            else:
                self.__lib = None
        else:
            raise RuntimeError("Unknown platform: %s" % sys.platform)

    @staticmethod
    def from_lib(name, lib):
        ret = Lib(name)
        ret.__lib = lib
        return ret

    def bind(self, name, arg_types, ret_type) -> Callable[[LibCall], LibCall]:
        if self.__lib is None:
            def decorator(f):
                @wraps(f)
                def wrapper(*args, **kwargs):
                    raise RuntimeError("Library %s is not initialized" % self.__name)
                return wrapper
            return decorator
        else:
            try:
                func = getattr(self.__lib, name)
            except AttributeError:
                # Name not found in library
                def decorator(f):
                    @wraps(f)
                    def wrapper(*args, **kwargs):
                        raise AttributeError("%s: undefined symbol: %s" % (self.__lib_path, name))
                    return wrapper
                logger.warning("Symbol %s not found in %s", name, self.__lib_path)
                return decorator
            func.argtypes = arg_types
            func.restype = ret_type
            setattr(self, name, func)
            
            def decorator(f):
                @wraps(f)
                def wrapper(*args, **kwargs):
                    return f(*args, **kwargs)
                return wrapper
            return decorator