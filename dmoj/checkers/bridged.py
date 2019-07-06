import os

from dmoj.error import CompileError, InternalError
from dmoj.executors import executors
from dmoj.executors.base_executor import CompiledExecutor
from dmoj.judgeenv import env, get_problem_root
from dmoj.result import CheckerResult
from dmoj.utils import ansi
from dmoj.utils.aux_files import compile_aux_files, _mktemp
from dmoj.utils.unicode import utf8text

checker_defaults = {
    'time_limit': env['generator_time_limit'],
    'memory_limit': env['generator_memory_limit'],
    'compiler_time_limit': env['compiler_time_limit'],
    'feedback': True
}

executor = None

def get_executor(checker_kwargs, problem_id):
    global executor

    if executor is None:
        if 'files' not in checker_kwargs:
            raise InternalError('No checker file[s] specified!')
        if 'lang' not in checker_kwargs:
            raise InternalError('Language not specified for checker!')

        filenames = list(map(lambda x: os.path.join(get_problem_root(problem_id), x), checker_kwargs['files']))
        lang = checker_kwargs['lang']
        executor = compile_aux_files(filenames, lang, checker_kwargs['compiler_time_limit'])

    return executor

def check(process_output, judge_output, judge_input, checker_kwargs, problem_id, point_value = None, **kwargs):
    checker_kwargs.update(checker_defaults)
    executor = get_executor(checker_kwargs, problem_id)

    with _mktemp(judge_input) as arg1, _mktemp(process_output) as arg2, _mktemp(judge_output) as arg3:
        process = executor.launch(arg1.name, arg2.name, arg3.name, memory=checker_kwargs['memory_limit'],
                                  time=checker_kwargs['time_limit'])

        proc_output, error = map(utf8text, process.communicate())

        # We use the testlib.h return codes
        AC = 0
        WA = 1
        PE = 2
        IE = 3

        if process.returncode == AC:
            if checker_kwargs['feedback']:
                return CheckerResult(True, point_value, feedback=proc_output)
            else:
                return True
        elif process.returncode in [WA, PE]:
            if checker_kwargs['feedback']:
                return CheckerResult(False, 0, feedback=proc_output)
            else:
                return CheckerResult(False, 0, feedback='Presentation Error' if process.returncode == PE else '')
        else:
            if process.returncode == IE:
                error = 'Checker failed assertion with message %s' % proc_output
            else:
                error = 'Checker returned unexpected return code %d with stderr %s' % (process.returncode, error)
            raise InternalError(error)
