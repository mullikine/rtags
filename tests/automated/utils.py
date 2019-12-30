import os.path
import subprocess as sp
import sys
import time


def is_exe(path):
    if not (os.path.isfile(path) and os.access(path, os.X_OK)):
        ValueError(path, 'file does not exist or is not executable')


class RTags():
    '''RTags class for rdm/rc tests'''

    try:
        __rdm_exe = os.path.join(os.environ['RTAGS_BINARY_DIR'], 'rdm')
        __rc_exe = os.path.join(os.environ['RTAGS_BINARY_DIR'], 'rc')
        is_exe(__rdm_exe)
        is_exe(__rc_exe)
    except KeyError:
        print('You need to set RTAGS_BINARY_DIR environment variable.', file=sys.stderr)
        sys.exit(1)
    except ValueError as err:
        print(str(err), file=sys.stderr)
        sys.exit(1)

    __sleep_time = 0.01     # Sleep time after command failed
    __max_retries = 1000    # Maximal retries when command failed (__sleep_time * __max_retries = 10 s)

    def __init__(self, socket_file=None):
        '''Init object.

        :param socket_file: The socket file, if not specified the default socket file will be used.
        '''
        self._socket_file = socket_file
        self._rdm_p = None

    def _add_args(self, sp_args, *args):
        '''Add ``*args`` to sp_args.

        Also add --socket-file argument right after the executable if not present and self._socket_file is set.
        :param sp_args: The subprocess argument list
        :param *args: Variable arguments
        '''
        for arg in args:
            if not isinstance(arg, str):
                # Unpack list/tuple
                self._add_args(sp_args, *arg)
            else:
                sp_args.append(arg)

        if not ('--socket-file' in sp_args or '-n' in sp_args) and self._socket_file:
            sp_args.insert(1, '--socket-file')
            sp_args.insert(2, self._socket_file)

    def rc(self, *args):
        '''Call rc with args.

        :params *args: Variable arguments
        '''
        rc_args = [self.__rc_exe]
        self._add_args(rc_args, args)
        return sp.check_output(rc_args).decode()

    def _rc_call_wait(self, *args):
        tries = 0
        while True:
            try:
                self.rc(args)
                time.sleep(self.__sleep_time)
                break
            except sp.CalledProcessError as err:
                if tries >= self.__max_retries:
                    print('Too many retries ({}): {} {} {} {}',
                          tries, err.returncode, err.cmd, err.output, err.stderr, file=sys.stderr)
                    sys.exit(1)
                time.sleep(self.__sleep_time)
                tries += 1

    def rdm(self, *args):
        '''Start rdm.

        :params *args: Variable arguments
        '''
        if self._rdm_p:
            return
        rdm_args = [self.__rdm_exe]
        self._add_args(rdm_args, args)
        self._rdm_p = sp.Popen(rdm_args, stdout=sp.PIPE, stderr=sp.STDOUT)
        self._rc_call_wait('-w')  # Wait until rdm is ready

    def rdm_quit(self):
        '''Quit rdm.'''
        self._rdm_p.terminate()
        self._rdm_p.wait()

    def parse(self, directory, files):
        '''Parse files from directory.

        :param directory: The files location
        :param files: The files to parse
        '''
        src_files = [os.path.join(directory, src_file) for src_file in files if src_file.endswith(('.cpp', '.c'))]
        compile_command_g = ('clang++ -std=c++11 -I. -c ' + src_file for src_file in src_files)
        count = 0

        for compile_command in compile_command_g:
            self.rc('--project-root', directory, '-c', compile_command)
            self._rc_call_wait('--is-indexed', src_files[count])  # Wait until the file is indexed
            count += 1
