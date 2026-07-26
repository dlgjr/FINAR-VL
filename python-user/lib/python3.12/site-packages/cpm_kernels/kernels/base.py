import ctypes
import os
from typing import List, Any, Tuple
from ..library import cuda, cudart
from ..device import Device
import pkg_resources
DevicePointer = int
CUDAStream = cudart.cudaStream_t

RESOURCE_PACKAGE_NAME = __name__

def round_up(x : int, m : int) -> int:
    return (x + m - 1) // m * m

class LazyKernelCModule:
    def __init__(self, code):
        self._code = code
        self._module = {}
    
    def get_module(self):
        curr_device = cudart.cudaGetDevice()
        if curr_device not in self._module:
            Device(curr_device).use()   # force initialize context
            self._module[curr_device] = cuda.cuModuleLoadData(self._code)
        return self._module[curr_device]



class KernelFunction:
    def __init__(self, cmodule : LazyKernelCModule, func_name : str) -> None:
        self._module = cmodule
        self._funcs = {}
        self._func_name = func_name
    
    def _prepare_func(self):
        curr_device = cudart.cudaGetDevice()
        cudart.cudaSetDevice(curr_device)   # ensure cudart context
        if curr_device not in self._funcs:
            self._funcs[curr_device] = cuda.cuModuleGetFunction(
                self._module.get_module(), self._func_name
            )
        return self._funcs[curr_device]
    
    def __call__(self, gridDim : Tuple[int, int, int], blockDim : Tuple[int, int, int], 
            sharedMemBytes : int, stream : cudart.cudaStream_t, params : List[Any] ) -> None:
        assert len(gridDim) == 3
        assert len(blockDim) == 3
        func = self._prepare_func()

        cuda.cuLaunchKernel(func, 
            gridDim[0], gridDim[1], gridDim[2], 
            blockDim[0], blockDim[1], blockDim[2], 
            sharedMemBytes, stream, [
                ctypes.addressof(p) for p in params
            ]
        )
        

class Kernel:
    def __init__(self, filename : str, function_names : List[str]):
        filename = filename + ".fatbin"
        filename = os.path.join("cuda", filename)
        if not pkg_resources.resource_exists(RESOURCE_PACKAGE_NAME, filename):
            raise RuntimeError("File `%s` not found in `%s`" % (filename, RESOURCE_PACKAGE_NAME))
        self.filename = filename
        self.code = pkg_resources.resource_string(RESOURCE_PACKAGE_NAME, filename)
        self._function_names = function_names
        self._cmodule = LazyKernelCModule(self.code)

        for name in self._function_names:
            setattr(self, name, KernelFunction(self._cmodule, name))






