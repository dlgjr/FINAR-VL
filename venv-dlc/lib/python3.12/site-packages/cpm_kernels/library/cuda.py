import ctypes
import sys
from typing import List
from .base import Lib

if sys.platform.startswith("win"):
    cuda = Lib.from_lib("cuda", ctypes.WinDLL("nvcuda.dll"))
else:
    cuda = Lib("cuda")
CUresult = ctypes.c_int

CUDA_SUCCESS = 0
#   The API call returned with no errors. In the case of query calls, this also means that the operation being queried is complete (see cuEventQuery() and cuStreamQuery()). 
CUDA_ERROR_INVALID_VALUE = 1
#   This indicates that one or more of the parameters passed to the API call is not within an acceptable range of values. 
CUDA_ERROR_OUT_OF_MEMORY = 2
#   The API call failed because it was unable to allocate enough memory to perform the requested operation. 
CUDA_ERROR_NOT_INITIALIZED = 3
#   This indicates that the CUDA driver has not been initialized with cuInit() or that initialization has failed. 
CUDA_ERROR_DEINITIALIZED = 4
#   This indicates that the CUDA driver is in the process of shutting down. 
CUDA_ERROR_PROFILER_DISABLED = 5
#   This indicates profiler is not initialized for this run. This can happen when the application is running with external profiling tools like visual profiler. 
CUDA_ERROR_PROFILER_NOT_INITIALIZED = 6
#   Deprecated
#   This error return is deprecated as of CUDA 5.0. It is no longer an error to attempt to enable/disable the profiling via cuProfilerStart or cuProfilerStop without initialization.
CUDA_ERROR_PROFILER_ALREADY_STARTED = 7
#   Deprecated
#   This error return is deprecated as of CUDA 5.0. It is no longer an error to call cuProfilerStart() when profiling is already enabled.
CUDA_ERROR_PROFILER_ALREADY_STOPPED = 8
#   Deprecated
#   This error return is deprecated as of CUDA 5.0. It is no longer an error to call cuProfilerStop() when profiling is already disabled.
CUDA_ERROR_STUB_LIBRARY = 34
#   This indicates that the CUDA driver that the application has loaded is a stub library. Applications that run with the stub rather than a real driver loaded will result in CUDA API returning this error. 
CUDA_ERROR_NO_DEVICE = 100
#   This indicates that no CUDA-capable devices were detected by the installed CUDA driver. 
CUDA_ERROR_INVALID_DEVICE = 101
#   This indicates that the device ordinal supplied by the user does not correspond to a valid CUDA device or that the action requested is invalid for the specified device. 
CUDA_ERROR_DEVICE_NOT_LICENSED = 102
#   This error indicates that the Grid license is not applied. 
CUDA_ERROR_INVALID_IMAGE = 200
#   This indicates that the device kernel image is invalid. This can also indicate an invalid CUDA module. 
CUDA_ERROR_INVALID_CONTEXT = 201
#   This most frequently indicates that there is no context bound to the current thread. This can also be returned if the context passed to an API call is not a valid handle (such as a context that has had cuCtxDestroy() invoked on it). This can also be returned if a user mixes different API versions (i.e. 3010 context with 3020 API calls). See cuCtxGetApiVersion() for more details. 
CUDA_ERROR_CONTEXT_ALREADY_CURRENT = 202
#   Deprecated
#   This error return is deprecated as of CUDA 3.2. It is no longer an error to attempt to push the active context via cuCtxPushCurrent().
#   This indicated that the context being supplied as a parameter to the API call was already the active context.
CUDA_ERROR_MAP_FAILED = 205
#   This indicates that a map or register operation has failed. 
CUDA_ERROR_UNMAP_FAILED = 206
#   This indicates that an unmap or unregister operation has failed. 
CUDA_ERROR_ARRAY_IS_MAPPED = 207
#   This indicates that the specified array is currently mapped and thus cannot be destroyed. 
CUDA_ERROR_ALREADY_MAPPED = 208
#   This indicates that the resource is already mapped. 
CUDA_ERROR_NO_BINARY_FOR_GPU = 209
#   This indicates that there is no kernel image available that is suitable for the device. This can occur when a user specifies code generation options for a particular CUDA source file that do not include the corresponding device configuration. 
CUDA_ERROR_ALREADY_ACQUIRED = 210
#   This indicates that a resource has already been acquired. 
CUDA_ERROR_NOT_MAPPED = 211
#   This indicates that a resource is not mapped. 
CUDA_ERROR_NOT_MAPPED_AS_ARRAY = 212
#   This indicates that a mapped resource is not available for access as an array. 
CUDA_ERROR_NOT_MAPPED_AS_POINTER = 213
#   This indicates that a mapped resource is not available for access as a pointer. 
CUDA_ERROR_ECC_UNCORRECTABLE = 214
#   This indicates that an uncorrectable ECC error was detected during execution. 
CUDA_ERROR_UNSUPPORTED_LIMIT = 215
#   This indicates that the CUlimit passed to the API call is not supported by the active device. 
CUDA_ERROR_CONTEXT_ALREADY_IN_USE = 216
#   This indicates that the CUcontext passed to the API call can only be bound to a single CPU thread at a time but is already bound to a CPU thread. 
CUDA_ERROR_PEER_ACCESS_UNSUPPORTED = 217
#   This indicates that peer access is not supported across the given devices. 
CUDA_ERROR_INVALID_PTX = 218
#   This indicates that a PTX JIT compilation failed. 
CUDA_ERROR_INVALID_GRAPHICS_CONTEXT = 219
#   This indicates an error with OpenGL or DirectX context. 
CUDA_ERROR_NVLINK_UNCORRECTABLE = 220
#   This indicates that an uncorrectable NVLink error was detected during the execution. 
CUDA_ERROR_JIT_COMPILER_NOT_FOUND = 221
#   This indicates that the PTX JIT compiler library was not found. 
CUDA_ERROR_UNSUPPORTED_PTX_VERSION = 222
#   This indicates that the provided PTX was compiled with an unsupported toolchain. 
CUDA_ERROR_JIT_COMPILATION_DISABLED = 223
#   This indicates that the PTX JIT compilation was disabled. 
CUDA_ERROR_UNSUPPORTED_EXEC_AFFINITY = 224
#   This indicates that the CUexecAffinityType passed to the API call is not supported by the active device. 
CUDA_ERROR_INVALID_SOURCE = 300
#   This indicates that the device kernel source is invalid. 
CUDA_ERROR_FILE_NOT_FOUND = 301
#   This indicates that the file specified was not found. 
CUDA_ERROR_SHARED_OBJECT_SYMBOL_NOT_FOUND = 302
#   This indicates that a link to a shared object failed to resolve. 
CUDA_ERROR_SHARED_OBJECT_INIT_FAILED = 303
#   This indicates that initialization of a shared object failed. 
CUDA_ERROR_OPERATING_SYSTEM = 304
#   This indicates that an OS call failed. 
CUDA_ERROR_INVALID_HANDLE = 400
#   This indicates that a resource handle passed to the API call was not valid. Resource handles are opaque types like CUstream and CUevent. 
CUDA_ERROR_ILLEGAL_STATE = 401
#   This indicates that a resource required by the API call is not in a valid state to perform the requested operation. 
CUDA_ERROR_NOT_FOUND = 500
#   This indicates that a named symbol was not found. Examples of symbols are global/constant variable names, driver function names, texture names, and surface names. 
CUDA_ERROR_NOT_READY = 600
#   This indicates that asynchronous operations issued previously have not completed yet. This result is not actually an error, but must be indicated differently than CUDA_SUCCESS (which indicates completion). Calls that may return this value include cuEventQuery() and cuStreamQuery(). 
CUDA_ERROR_ILLEGAL_ADDRESS = 700
#   While executing a kernel, the device encountered a load or store instruction on an invalid memory address. This leaves the process in an inconsistent state and any further CUDA work will return the same error. To continue using CUDA, the process must be terminated and relaunched. 
CUDA_ERROR_LAUNCH_OUT_OF_RESOURCES = 701
#   This indicates that a launch did not occur because it did not have appropriate resources. This error usually indicates that the user has attempted to pass too many arguments to the device kernel, or the kernel launch specifies too many threads for the kernel's register count. Passing arguments of the wrong size (i.e. a 64-bit pointer when a 32-bit int is expected) is equivalent to passing too many arguments and can also result in this error. 
CUDA_ERROR_LAUNCH_TIMEOUT = 702
#   This indicates that the device kernel took too long to execute. This can only occur if timeouts are enabled - see the device attribute CU_DEVICE_ATTRIBUTE_KERNEL_EXEC_TIMEOUT for more information. This leaves the process in an inconsistent state and any further CUDA work will return the same error. To continue using CUDA, the process must be terminated and relaunched. 
CUDA_ERROR_LAUNCH_INCOMPATIBLE_TEXTURING = 703
#   This error indicates a kernel launch that uses an incompatible texturing mode. 
CUDA_ERROR_PEER_ACCESS_ALREADY_ENABLED = 704
#   This error indicates that a call to cuCtxEnablePeerAccess() is trying to re-enable peer access to a context which has already had peer access to it enabled. 
CUDA_ERROR_PEER_ACCESS_NOT_ENABLED = 705
#   This error indicates that cuCtxDisablePeerAccess() is trying to disable peer access which has not been enabled yet via cuCtxEnablePeerAccess(). 
CUDA_ERROR_PRIMARY_CONTEXT_ACTIVE = 708
#   This error indicates that the primary context for the specified device has already been initialized. 
CUDA_ERROR_CONTEXT_IS_DESTROYED = 709
#   This error indicates that the context current to the calling thread has been destroyed using cuCtxDestroy, or is a primary context which has not yet been initialized. 
CUDA_ERROR_ASSERT = 710
#   A device-side assert triggered during kernel execution. The context cannot be used anymore, and must be destroyed. All existing device memory allocations from this context are invalid and must be reconstructed if the program is to continue using CUDA. 
CUDA_ERROR_TOO_MANY_PEERS = 711
#   This error indicates that the hardware resources required to enable peer access have been exhausted for one or more of the devices passed to cuCtxEnablePeerAccess(). 
CUDA_ERROR_HOST_MEMORY_ALREADY_REGISTERED = 712
#   This error indicates that the memory range passed to cuMemHostRegister() has already been registered. 
CUDA_ERROR_HOST_MEMORY_NOT_REGISTERED = 713
#   This error indicates that the pointer passed to cuMemHostUnregister() does not correspond to any currently registered memory region. 
CUDA_ERROR_HARDWARE_STACK_ERROR = 714
#   While executing a kernel, the device encountered a stack error. This can be due to stack corruption or exceeding the stack size limit. This leaves the process in an inconsistent state and any further CUDA work will return the same error. To continue using CUDA, the process must be terminated and relaunched. 
CUDA_ERROR_ILLEGAL_INSTRUCTION = 715
#   While executing a kernel, the device encountered an illegal instruction. This leaves the process in an inconsistent state and any further CUDA work will return the same error. To continue using CUDA, the process must be terminated and relaunched. 
CUDA_ERROR_MISALIGNED_ADDRESS = 716
#   While executing a kernel, the device encountered a load or store instruction on a memory address which is not aligned. This leaves the process in an inconsistent state and any further CUDA work will return the same error. To continue using CUDA, the process must be terminated and relaunched. 
CUDA_ERROR_INVALID_ADDRESS_SPACE = 717
#   While executing a kernel, the device encountered an instruction which can only operate on memory locations in certain address spaces (global, shared, or local), but was supplied a memory address not belonging to an allowed address space. This leaves the process in an inconsistent state and any further CUDA work will return the same error. To continue using CUDA, the process must be terminated and relaunched. 
CUDA_ERROR_INVALID_PC = 718
#   While executing a kernel, the device program counter wrapped its address space. This leaves the process in an inconsistent state and any further CUDA work will return the same error. To continue using CUDA, the process must be terminated and relaunched. 
CUDA_ERROR_LAUNCH_FAILED = 719
#   An exception occurred on the device while executing a kernel. Common causes include dereferencing an invalid device pointer and accessing out of bounds shared memory. Less common cases can be system specific - more information about these cases can be found in the system specific user guide. This leaves the process in an inconsistent state and any further CUDA work will return the same error. To continue using CUDA, the process must be terminated and relaunched. 
CUDA_ERROR_COOPERATIVE_LAUNCH_TOO_LARGE = 720
#   This error indicates that the number of blocks launched per grid for a kernel that was launched via either cuLaunchCooperativeKernel or cuLaunchCooperativeKernelMultiDevice exceeds the maximum number of blocks as allowed by cuOccupancyMaxActiveBlocksPerMultiprocessor or cuOccupancyMaxActiveBlocksPerMultiprocessorWithFlags times the number of multiprocessors as specified by the device attribute CU_DEVICE_ATTRIBUTE_MULTIPROCESSOR_COUNT. 
CUDA_ERROR_NOT_PERMITTED = 800
#   This error indicates that the attempted operation is not permitted. 
CUDA_ERROR_NOT_SUPPORTED = 801
#   This error indicates that the attempted operation is not supported on the current system or device. 
CUDA_ERROR_SYSTEM_NOT_READY = 802
#   This error indicates that the system is not yet ready to start any CUDA work. To continue using CUDA, verify the system configuration is in a valid state and all required driver daemons are actively running. More information about this error can be found in the system specific user guide. 
CUDA_ERROR_SYSTEM_DRIVER_MISMATCH = 803
#   This error indicates that there is a mismatch between the versions of the display driver and the CUDA driver. Refer to the compatibility documentation for supported versions. 
CUDA_ERROR_COMPAT_NOT_SUPPORTED_ON_DEVICE = 804
#   This error indicates that the system was upgraded to run with forward compatibility but the visible hardware detected by CUDA does not support this configuration. Refer to the compatibility documentation for the supported hardware matrix or ensure that only supported hardware is visible during initialization via the CUDA_VISIBLE_DEVICES environment variable. 
CUDA_ERROR_MPS_CONNECTION_FAILED = 805
#   This error indicates that the MPS client failed to connect to the MPS control daemon or the MPS server. 
CUDA_ERROR_MPS_RPC_FAILURE = 806
#   This error indicates that the remote procedural call between the MPS server and the MPS client failed. 
CUDA_ERROR_MPS_SERVER_NOT_READY = 807
#   This error indicates that the MPS server is not ready to accept new MPS client requests. This error can be returned when the MPS server is in the process of recovering from a fatal failure. 
CUDA_ERROR_MPS_MAX_CLIENTS_REACHED = 808
#   This error indicates that the hardware resources required to create MPS client have been exhausted. 
CUDA_ERROR_MPS_MAX_CONNECTIONS_REACHED = 809
#   This error indicates the the hardware resources required to support device connections have been exhausted. 
CUDA_ERROR_STREAM_CAPTURE_UNSUPPORTED = 900
#   This error indicates that the operation is not permitted when the stream is capturing. 
CUDA_ERROR_STREAM_CAPTURE_INVALIDATED = 901
#   This error indicates that the current capture sequence on the stream has been invalidated due to a previous error. 
CUDA_ERROR_STREAM_CAPTURE_MERGE = 902
#   This error indicates that the operation would have resulted in a merge of two independent capture sequences. 
CUDA_ERROR_STREAM_CAPTURE_UNMATCHED = 903
#   This error indicates that the capture was not initiated in this stream. 
CUDA_ERROR_STREAM_CAPTURE_UNJOINED = 904
#   This error indicates that the capture sequence contains a fork that was not joined to the primary stream. 
CUDA_ERROR_STREAM_CAPTURE_ISOLATION = 905
#   This error indicates that a dependency would have been created which crosses the capture sequence boundary. Only implicit in-stream ordering dependencies are allowed to cross the boundary. 
CUDA_ERROR_STREAM_CAPTURE_IMPLICIT = 906
#   This error indicates a disallowed implicit dependency on a current capture sequence from cudaStreamLegacy. 
CUDA_ERROR_CAPTURED_EVENT = 907
#   This error indicates that the operation is not permitted on an event which was last recorded in a capturing stream. 
CUDA_ERROR_STREAM_CAPTURE_WRONG_THREAD = 908
#   A stream capture sequence not initiated with the CU_STREAM_CAPTURE_MODE_RELAXED argument to cuStreamBeginCapture was passed to cuStreamEndCapture in a different thread. 
CUDA_ERROR_TIMEOUT = 909
#   This error indicates that the timeout specified for the wait operation has lapsed. 
CUDA_ERROR_GRAPH_EXEC_UPDATE_FAILURE = 910
#   This error indicates that the graph update was not performed because it included changes which violated constraints specific to instantiated graph update. 
CUDA_ERROR_EXTERNAL_DEVICE = 911
#   This indicates that an async error has occurred in a device outside of CUDA. If CUDA was waiting for an external device's signal before consuming shared data, the external device signaled an error indicating that the data is not valid for consumption. This leaves the process in an inconsistent state and any further CUDA work will return the same error. To continue using CUDA, the process must be terminated and relaunched. 
CUDA_ERROR_UNKNOWN = 999
#   This indicates that an unknown internal error has occurred. 

CUmodule = ctypes.c_void_p
CUfunction = ctypes.c_void_p
CUcontext = ctypes.c_void_p

### Error handling

@cuda.bind("cuGetErrorName", [CUresult, ctypes.POINTER(ctypes.c_char_p)], CUresult)
def cuGetErrorName(error : int) -> str:
    ptr = ctypes.c_char_p()
    status = cuda.cuGetErrorName(error, ctypes.byref(ptr))
    if status == CUDA_ERROR_INVALID_VALUE:
        raise RuntimeError("Invalid error value: %d", error)
    return ptr.value.decode()

@cuda.bind("cuGetErrorString", [CUresult, ctypes.POINTER(ctypes.c_char_p)], CUresult)
def cuGetErrorString(error : int) -> str:
    ptr = ctypes.c_char_p()
    status = cuda.cuGetErrorString(error, ctypes.byref(ptr))
    if status == CUDA_ERROR_INVALID_VALUE:
        raise RuntimeError("Invalid error value: %d", error)
    return ptr.value.decode()

def checkCUStatus(error : int) -> None:
    if error != CUDA_SUCCESS:
        raise RuntimeError("CUDA Error: %s" % cuGetErrorString(error))

@cuda.bind("cuDriverGetVersion", [ctypes.POINTER(ctypes.c_int)], CUresult)
def cuDriverGetVersion() -> int:
    version = ctypes.c_int()
    checkCUStatus(cuda.cuDriverGetVersion(ctypes.byref(version)))
    return version.value

try:
    version = cuDriverGetVersion()
except RuntimeError:
    version = 0


@cuda.bind("cuModuleLoadData", [ctypes.POINTER(CUmodule), ctypes.c_void_p], CUresult)
def cuModuleLoadData(data : bytes) -> CUmodule:
    module = CUmodule()
    checkCUStatus(cuda.cuModuleLoadData(ctypes.byref(module), data))
    return module

@cuda.bind("cuModuleUnload", [CUmodule], CUresult)
def cuModuleUnload(module : CUmodule) -> None:
    checkCUStatus(cuda.cuModuleUnload(module))


@cuda.bind("cuModuleGetFunction", [ctypes.POINTER(CUfunction), CUmodule, ctypes.c_char_p], CUresult)
def cuModuleGetFunction(module : CUmodule, name : str) -> CUfunction:
    function = CUfunction()
    checkCUStatus(cuda.cuModuleGetFunction(ctypes.byref(function), module, name.encode()))
    return function

### Execution control

@cuda.bind("cuLaunchKernel", [
    CUfunction, 
    ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, 
    ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, 
    ctypes.c_uint, 
    ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_void_p)], CUresult)
def cuLaunchKernel(
    func : CUfunction,
    gridDimX : int, gridDimY : int, gridDimZ : int,
    blockDimX : int, blockDimY : int, blockDimZ : int,
    sharedMemBytes : int,
    hStream : ctypes.c_void_p,
    kernelParams : List[int]
):
    if len(kernelParams) > 0:
        kernelParams = (ctypes.c_void_p * len(kernelParams))(*kernelParams)
    else:
        kernelParams = None
    checkCUStatus(cuda.cuLaunchKernel(func, gridDimX, gridDimY, gridDimZ, blockDimX, blockDimY, blockDimZ, sharedMemBytes, hStream, kernelParams, None))

@cuda.bind("cuCtxGetCurrent", [ctypes.POINTER(CUcontext)], CUresult)
def cuCtxGetCurrent() -> CUcontext:
    context = CUcontext()
    checkCUStatus(cuda.cuCtxGetCurrent(ctypes.byref(context)))
    return context
