"""
   Copyright 2014 n@work Internet Informationssysteme GmbH, Germany

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

import argparse
import fnmatch
import os
import sys
from tarfile import TarFile
from cStringIO import StringIO


class DockerIgnoreParser(object):
    def __init__(self, ignore_string):
        self.ignore_rules = [self._mangle(line) for line in ignore_string.split('\n') if line]

    def _mangle(self, line):
        if line.endswith('/'):
            # Everything gets passed through os.path.relpath which *strips* trailing slashes
            line = line[:-1]
        return line

    def ignores(self, filename):
        return any(fnmatch.fnmatchcase(filename, pattern) for pattern in self.ignore_rules)

    @classmethod
    def from_filename(cls, filename):
        with open(filename, 'r') as f:
            return cls(f.read())

    @classmethod
    def from_file_obj(cls, file_obj):
        return cls(file_obj.read())


class DockerContextGenerator(object):
    def __init__(self, context, dockerfile, filter_list, replacement_list, dockerignore):
        self.context = context
        self.filter_list = filter_list
        self.replacement_list = replacement_list
        self.dockerfile = dockerfile
        self.dockerignore = dockerignore

    def filter_func(self, info=None, prefix=None):
        def inner(info):
            path = os.path.relpath(info.name)
            if prefix is not None and path.startswith(prefix):
                path = path[len(prefix) + 1:]

            in_filter_list = path in self.filter_list

            if self.dockerignore is not None:
                ignored = self.dockerignore.ignores(path)
            else:
                ignored = False

            if in_filter_list or ignored:
                return None
            else:
                return info
        if prefix is None:
            return inner(info)
        else:
            return inner

    def create_context(self):
        stringfile = StringIO()
        with TarFile.open(mode='w', fileobj=stringfile) as tarfile:
            tarfile.add(self.context, arcname='.', filter=self.filter_func)
            for src, dst in self.replacement_list:
                tarfile.add(src, arcname=os.path.join('.', dst), filter=self.filter_func(prefix=dst))
            if self.dockerfile:
                tarfile.add(self.dockerfile, arcname='./Dockerfile')
        stringfile.seek(0)
        return stringfile.read()


def main():
    parser = argparse.ArgumentParser(description='Replace Dockerfile and/or replace file path in context')
    parser.add_argument('context', type=str, action='store', help='path to context')
    parser.add_argument('-p', '--path', metavar='PATH', type=str, dest='paths', action='append',
                        default=[], help='Path to insert into context, e.g. extra_context:where_to_put_it')
    parser.add_argument('-d', '--dockerfile', metavar='DOCKERFILE', type=str, dest='dockerfile', default=None,
                        action='store', help='replacement dockerfile')
    parser.add_argument('-i', '--dockerignore', default=None,
                        help='A file containing glob rules for which files to exclude from the context. '
                        '.dockerignore will be used by default if it exists.')
    parsed = parser.parse_args()

    filter_list = []
    replacement_list = []
    dockerfile = None

    if parsed.dockerfile is not None:
        filter_list.append('Dockerfile')
        dockerfile = parsed.dockerfile
        if not os.path.isfile(dockerfile):
            parser.error('DOCKERFILE is expected to be a plain file')

    if parsed.dockerignore is not None:
        if not os.path.isfile(parsed.dockerignore):
            parser.error('DOCKERIGNORE must be a file')
        dockerignore = DockerIgnoreParser.from_filename(parsed.dockerignore)
    else:
        if os.path.isfile('.dockerignore'):
            dockerignore = DockerIgnoreParser.from_filename('.dockerignore')
        else:
            dockerignore = None

    for path in parsed.paths:
        try:
            (source, dest) = path.split(':')
        except:
            parser.error('wrong path syntax')
        replacement_list.append((source, dest))

    dcg = DockerContextGenerator(os.path.relpath(parsed.context),
                                 dockerfile,
                                 filter_list,
                                 replacement_list,
                                 dockerignore)
    tarstring = dcg.create_context()
    sys.stdout.write(tarstring)

if __name__ == '__main__':
    main()
