import enum
import json
import os
import os.path

import pytest

import utils

TESTS = None
TESTS_NAME = None


@pytest.yield_fixture(scope='module', autouse=True)
def rtags(tmpdir_factory):
    '''RTags session yield fixture.

    Start rdm and return the RTags object.
    At the and of the session the rdm process will be stopped.

    :param tmpdir_factory: The tmpdir_factory fixture
    '''
    rtags = utils.RTags('/var/tmp/rdm_dev')
    rtags.rdm('--data-dir', str(tmpdir_factory.mktemp('data_dir')), '--no-filesystem-watcher', '--log-flush')
    yield rtags
    rtags.rdm_quit()


class Location():
    '''Class representing location in file.'''

    def __init__(self, file, line, col):
        self.file, self.line, self.col = str(file), int(line), int(col)

    @classmethod
    def from_str(cls, string):
        '''From string.'''
        return cls(*string.split(':')[0:3])

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            raise ValueError('Type error')

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return '%s:%d:%d' % (self.file, self.line, self.col)


class TType(enum.IntEnum):
    '''Enum class representing the test types we support.'''
    LOCATION = 1
    PARSE = 2
    COMPLETION = 3
    OUTPUT = 4

    @classmethod
    def get(cls, test_dir):
        '''Return test type derived from the directory name.'''
        if 'Parsing' in test_dir:
            return cls.PARSE

        if 'Completion' in test_dir:
            return cls.COMPLETION

        if 'Output' in test_dir:
            return cls.OUTPUT

        return cls.LOCATION


def collect_tests():
    '''Helper function to gather all tests and to not pollute the global scope.'''
    global TESTS, TESTS_NAME

    TESTS = {t: [] for t in TType}
    TESTS_NAME = {t: [] for t in TType}

    for test_dir, _, test_files in tuple(os.walk(os.path.dirname(os.path.abspath(__file__))))[1:]:
        if 'expectation.json' not in test_files:
            continue

        ttype = TType.get(os.path.basename(test_dir))
        expectations = json.load(open(os.path.join(test_dir, 'expectation.json'), 'r'))
        TESTS[ttype].append([test_dir, test_files, expectations])
        TESTS_NAME[ttype].append(os.path.basename(test_dir))


###
# Collect all tests
###
collect_tests()

###
# Tests
###
@pytest.mark.parametrize('directory,files,expectations', TESTS[TType.LOCATION], ids=TESTS_NAME[TType.LOCATION])
def test_location(directory, files, expectations, rtags):
    rtags.parse(directory, files)
    for exp in expectations:
        expected_locations = exp['expectation']
        actual_locations = [
            Location(os.path.join(directory, line.split(':')[0]), line.split(':')[1], line.split(':')[2])
            for line in
            rtags.rc([c.format(directory) for c in exp['rc-command']]).split('\n')
            if len(line) > 0
        ]
        # Compare that we have the same results in length and content
        assert len(actual_locations) == len(expected_locations)
        for expected_location_string in expected_locations:
            expected_location = Location.from_str(expected_location_string.format(directory))
            assert expected_location in actual_locations


@pytest.mark.parametrize('directory,files,expectations', TESTS[TType.PARSE], ids=TESTS_NAME[TType.PARSE])
def test_parse(directory, files, expectations, rtags):
    rtags.parse(directory, files)
    for exp in expectations:
        output = rtags.rc(exp['rc-command'])
        assert output
        assert exp['expectation'].format(directory + '/') in output.split()


@pytest.mark.parametrize('directory,files,expectations', TESTS[TType.COMPLETION], ids=TESTS_NAME[TType.COMPLETION])
def test_completion(directory, files, expectations, rtags):
    rtags.parse(directory, files)
    for exp in expectations:
        expected = exp['expectation']
        outputs = rtags.rc([c.format(directory) for c in exp['rc-command']]).split('\n')
        assert len(outputs) == len(expected)
        for output in outputs:
            assert output in expected


@pytest.mark.parametrize('directory,files,expectations', TESTS[TType.OUTPUT], ids=TESTS_NAME[TType.OUTPUT])
def test_output(directory, files, expectations, rtags):
    rtags.parse(directory, files)
    for exp in expectations:
        expected = exp['expectation']
        actual_outputs = [
            line
            for line in
            rtags.rc([c.format(directory) for c in exp['rc-command']]).split('\n')
            if len(line) > 0
        ]
        # Compare that we have the same results in length and content
        assert len(expected) == len(actual_outputs)
        for expected_output_string in expected:
            expected_output = expected_output_string.format(directory)
            assert expected_output in actual_outputs
