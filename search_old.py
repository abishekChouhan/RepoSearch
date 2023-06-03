import os
import sys
import argparse
import asyncio
import hashlib


def get_args():
    '''
    Parse required arguments
    '''
    args = argparse.ArgumentParser(description='Takes a [directory] git repo and a '
                                               '[source] file as input and search all '
                                               'the copies of code in source file '
                                               'anywhere in the git repo.')
    args.add_argument('-repo_path', required=True,
                      type=str, help='the path to repo')
    args.add_argument('-source_file', required=True,
                      type=str, help='the path to source file')
    args = args.parse_args()
    return args


class RepoSearchException(Exception):
    pass









class RepoSearch(object):
    '''
    Search the repository against a source file.
    '''

    def __init__(self, repo_path, source_file):
        '''
        Constructor
        para:: repo_path: Path the repository where we need to search
        para:: source_file: Path to source file
        '''
        self.repo_path = repo_path
        self.source_file = source_file
        self.source_file_data = None
        self.source_file_hash = None

    @staticmethod
    def _get_hash(bytes_string):
        hash_object = hashlib.sha256(bytes_string)
        return hash_object.hexdigest()

    def _is_match(self, item_file):
        '''
        Match one file against the source file
        TO-DO: The functionality can be extended to search line by line using regex ('re' module)
        '''
        # Match by file size
        try:
            if os.path.getsize(self.source_file) != os.path.getsize(item_file):
                return False
        except OSError:
            return False

        # Match SHA256
        with open(item_file, 'r', encoding="utf-8", errors='replace') as file:
            data = file.read().encode()
            item_file_hash = RepoSearch._get_hash(data)
        if self.source_file_hash != item_file_hash:
            return False
        return True

    def _list_files_and_dirs(self, target_dir):
        dirs, files = [], []
        try:
            for item in os.listdir(target_dir):
                # ignore hidden dir
                if item[0] != ".":
                    item_path = os.path.join(target_dir, item)
                    if os.path.isdir(item_path):
                        dirs.append(item_path)
                    else:
                        if self._is_match(item_path):
                            files.append(item_path)
        except PermissionError:
            raise RepoSearchException(f'Permission denied. Can\'t access directory `{target_dir}`.')
        return dirs, files

    async def _rec_traverse_repo(self, target_dir):
        '''
        Generator
        Recursively loop through the directories and search the match
        Yields each file from bottom-up
        '''
        try:
            dirs, files = self._list_files_and_dirs(target_dir)
            for _dir in dirs:
                async for _file in self._rec_traverse_repo(_dir):
                    yield _file

            for _file in files:
                yield _file
        except RepoSearchException as err:
            print(err)

    async def _search(self):
        '''
        Start search
        '''
        if not os.path.isfile(self.source_file):
            raise RepoSearchException(f'Source file `{self.source_file}` doesn\'t exist.')
        if not os.path.isdir(self.repo_path):
            raise RepoSearchException(f'Directory `{self.repo_path}` doesn\'t exist.')
        with open(self.source_file, 'r', encoding="utf-8", errors='replace') as src:
            self.source_file_data = src.read()
            if self.source_file_data == '':
                raise RepoSearchException(f'Empty source file.')
        self.source_file_hash = RepoSearch._get_hash(self.source_file_data.encode())
        print('Matches: ')
        match_found = False
        async for i in self._rec_traverse_repo(self.repo_path):
            if i != self.source_file:
                match_found = True
                print(f"\t{i}")
        if not match_found:
            print('No match found')

    def run(self):
        '''
        Starts the async loop and search
        '''
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self._search())
        except RepoSearchException as err:
            raise RepoSearchException(err)


if __name__ == '__main__':
    args = get_args()
    search = RepoSearch(repo_path=args.repo_path, source_file=args.source_file)
    try:
        search.run()
    except RepoSearchException as err:
        print(err)
        sys.exit(-1)
