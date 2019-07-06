import os
import tempfile
import traceback

from dmoj.error import CompileError, InternalError
from dmoj.executors import executors
from dmoj.executors.base_executor import CompiledExecutor


def _mktemp(data):
    tmp = tempfile.NamedTemporaryFile()
    tmp.write(data)
    tmp.flush()
    return tmp


def compile_aux_files(filenames, lang=None, compile_time_limit=None):
    sources = {}

    try:
        for filename in filenames:
            with open(filename, 'r') as f:
                sources[os.path.basename(filename)] = f.read()
    except:
        traceback.print_exc()
        raise IOError('Could not read source!')

    def find_runtime(languages):
        for grader in languages:
            if grader in executors:
                return grader
        return None

    use_cpp = any(map(lambda name: os.path.splitext(name)[1] in ['.cpp', '.cc'], filenames))
    if lang is None:
        best_choices = ('CPP17', 'CPP14', 'CPP11', 'CPP0X', 'CPP03') if use_cpp else ('C11', 'C')
        lang = find_runtime(best_choices)

    clazz = executors.get(lang)
    if not clazz:
        raise IOError('could not find an appropriate C++ executor')

    clazz = clazz.Executor

    fs = clazz.fs + [tempfile.gettempdir()]
    clazz = type('Executor', (clazz,), {'fs': fs})

    if issubclass(clazz, CompiledExecutor):
        compiler_time_limit = compile_time_limit or clazz.compiler_time_limit
        clazz = type('Executor', (clazz,), {'compiler_time_limit': compiler_time_limit})

    # Optimize the common case.
    if use_cpp:
        # Some auxilary files (like those using testlib.h) take an extremely long time to compile, so we cache them.
        executor = clazz('_aux_file', None, aux_sources=sources, cached=True)
    else:
        if len(sources) > 1:
            raise InternalError('non-C/C++ auxilary programs cannot be multi-file')
        executor = clazz('_generator', list(sources.values())[0])

    return executor
