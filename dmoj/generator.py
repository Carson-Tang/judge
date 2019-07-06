import os


class GeneratorManager:
    def get_generator(self, filenames, flags, lang=None, compiler_time_limit=None):
        filenames = list(map(os.path.abspath, filenames))
        return compile_aux_files(filenames, lang, compiler_time_limit)
