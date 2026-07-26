import ctypes
from typing import List, Tuple
from .base import Lib

nvrtc = Lib("nvrtc")

nvrtcResult = ctypes.c_int
NVRTC_SUCCESS = 0
NVRTC_ERROR_OUT_OF_MEMORY = 1
NVRTC_ERROR_PROGRAM_CREATION_FAILURE = 2
NVRTC_ERROR_INVALID_INPUT = 3
NVRTC_ERROR_INVALID_PROGRAM = 4
NVRTC_ERROR_INVALID_OPTION = 5
NVRTC_ERROR_COMPILATION = 6
NVRTC_ERROR_BUILTIN_OPERATION_FAILURE = 7
NVRTC_ERROR_NO_NAME_EXPRESSIONS_AFTER_COMPILATION = 8
NVRTC_ERROR_NO_LOWERED_NAMES_BEFORE_COMPILATION = 9
NVRTC_ERROR_NAME_EXPRESSION_NOT_VALID = 10
NVRTC_ERROR_INTERNAL_ERROR = 11

nvrtcProgram = ctypes.c_void_p

@nvrtc.bind("nvrtcGetErrorString", [nvrtcResult], ctypes.c_char_p)
def nvrtcGetErrorString(status : int) -> str:
    return nvrtc.nvrtcGetErrorString(status).decode()

def checkNVRTCStatus(status : int):
    if status == 0:
        return
    raise RuntimeError("NVRTC Error: %s" % nvrtcGetErrorString(status))

@nvrtc.bind("nvrtcVersion", [ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)], nvrtcResult)
def nvrtcVersion() -> Tuple[int, int]:
    major = ctypes.c_int()
    minor = ctypes.c_int()
    checkNVRTCStatus( nvrtc.nvrtcVersion(ctypes.byref(major), ctypes.byref(minor)) )
    return (major.value, minor.value)

try:
    version = nvrtcVersion()
except RuntimeError:
    version = (0, 0)

@nvrtc.bind("nvrtcCompileProgram", [nvrtcProgram, ctypes.c_int, ctypes.POINTER(ctypes.c_char_p)], nvrtcResult)
def nvrtcCompileProgram(prog : nvrtcProgram, numOptions : int, options : List[str]):
    lstType = ctypes.c_char_p * numOptions
    lst = [
        ctypes.c_char_p(opt.encode()) for opt in options
    ]
    options = lstType(*lst)
    status = nvrtc.nvrtcCompileProgram(prog, numOptions, options)
    if status == NVRTC_ERROR_COMPILATION:
        psize = nvrtcGetProgramLogSize(prog)
        log = ctypes.create_string_buffer(psize)
        nvrtcGetProgramLog(prog, log)
        raise RuntimeError(
            "NVRTC Error: NVRTC ERROR COMPILATION\n%s" % log.value.decode()
        )
    else:
        checkNVRTCStatus( status )

@nvrtc.bind("nvrtcCreateProgram", [ ctypes.POINTER(nvrtcProgram), ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.POINTER(ctypes.c_char_p), ctypes.POINTER(ctypes.c_char_p) ], nvrtcResult)
def nvrtcCreateProgram(prog : nvrtcProgram, src : str, name : str, numHeaders : int, headers : List[str], includeNames : List[str]):
    headers = [
        ctypes.c_char_p(header.encode()) for header in headers
    ]
    headers = (ctypes.c_char_p * numHeaders)(*headers)

    includeNames = [
        ctypes.c_char_p(includeName.encode()) for includeName in includeNames
    ]
    includeNames = (ctypes.c_char_p * numHeaders)(*includeNames)
    checkNVRTCStatus( nvrtc.nvrtcCreateProgram(ctypes.byref(prog), src.encode(), name.encode(), numHeaders, headers, includeNames) )


@nvrtc.bind("nvrtcDestroyProgram", [ ctypes.POINTER(nvrtcProgram) ], nvrtcResult)
def nvrtcDestroyProgram(prog : nvrtcProgram):
    checkNVRTCStatus( nvrtc.nvrtcDestroyProgram( ctypes.byref(prog)) )

if version[0] >= 11:
    @nvrtc.bind("nvrtcGetCUBIN", [nvrtcProgram, ctypes.c_char_p], nvrtcResult)
    def nvrtcGetCUBIN(prog : nvrtcProgram, buf : ctypes.c_char_p):
        checkNVRTCStatus( nvrtc.nvrtcGetCUBIN(prog, buf) )

    @nvrtc.bind("nvrtcGetCUBINSize", [nvrtcProgram, ctypes.POINTER(ctypes.c_size_t)], nvrtcResult)
    def nvrtcGetCUBINSize(prog) -> int:
        size = ctypes.c_size_t()
        checkNVRTCStatus( nvrtc.nvrtcGetCUBINSize(prog, ctypes.byref(size)) )
        return size.value

@nvrtc.bind("nvrtcGetPTX", [nvrtcProgram, ctypes.c_char_p], nvrtcResult)
def nvrtcGetPTX(prog, buf):
    checkNVRTCStatus( nvrtc.nvrtcGetPTX(prog, buf) )

@nvrtc.bind("nvrtcGetPTXSize", [nvrtcProgram, ctypes.POINTER(ctypes.c_size_t)], nvrtcResult)
def nvrtcGetPTXSize(prog) -> int:
    size = ctypes.c_size_t()
    checkNVRTCStatus( nvrtc.nvrtcGetPTXSize(prog, ctypes.byref(size)) )
    return size.value

@nvrtc.bind("nvrtcGetProgramLog", [nvrtcProgram, ctypes.c_char_p], nvrtcResult)
def nvrtcGetProgramLog(prog, buf):
    checkNVRTCStatus( nvrtc.nvrtcGetProgramLog(prog, buf) )

@nvrtc.bind("nvrtcGetProgramLogSize", [nvrtcProgram, ctypes.POINTER(ctypes.c_size_t)], nvrtcResult)
def nvrtcGetProgramLogSize(prog) -> int:
    size = ctypes.c_size_t()
    checkNVRTCStatus( nvrtc.nvrtcGetProgramLogSize(prog, ctypes.byref(size)) )
    return size.value
