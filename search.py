import os
import sys
import argparse
import time
# from queue import Queue
# from threading import Thread, Lock

## Using Multiprocessing module inplace of Multithreading. Because it is giving 4x performance
from multiprocessing import Process as Thread
from multiprocessing import Manager, Queue


IGNORE_EXTENSIONS = ['zip', 'jpg', 'mp4', 'mp3', 'png', 'h5', 'csv', 'dat']


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
    args.add_argument('-num_threads', required=False, default=4,
                      type=int, help='Number of worker thread to run')
    args = args.parse_args()
    return args


class RepoSearchException(Exception):
    pass


class RepoSearch(object):
    '''
    Search the repository against a source file.
    '''

    def __init__(self, repo_path, source_file, num_workers=2):
        '''
        Constructor
        para:: repo_path: Path the repository where we need to search
        para:: source_file: Path to source file
        para:: num_workers: Number of worker threads to run
        '''
        self.repo_path = repo_path
        self.source_file = source_file
        self.source_file_data = None
        self.queue = Queue()
        self.num_workers = num_workers
        self.stop_signal = '__stop__this__thread__'
        if 'multiprocessing' in str(Thread):
            manager = Manager()
            self.matches = manager.dict()
        else:
            self.matches = {}
        self.workers = []
        self.file_count = 0
        self.dir_count = 1
        self.ignored_file_count = 0

    def _find_match_in_file(self, curr_file):
        '''
        Match one file against the source file
        Used dynamic programming for find command blocks of lines in the current file which matches the source file.
        '''
        with open(curr_file, 'r', encoding="utf-8", errors='replace') as file:
            curr_file_data = file.readlines()

        n = len(self.source_file_data)
        m = len(curr_file_data)
        dp = [[0 for _ in range(m + 1)] for _ in range(n + 1)]
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                if self.source_file_data[i - 1] == curr_file_data[j - 1]:
                    if self.source_file_data[i - 1].strip() == '' and dp[i - 1][j - 1] == 0:
                        dp[i][j] = 0
                    else:
                        dp[i][j] = 1 + dp[i - 1][j - 1]
                        dp[i - 1][j - 1] = 0
                else:
                    dp[i][j] = 0
        matches = []
        for i in range(n + 1):
            for j in range(m + 1):
                # only consider if match is of more than one line
                if dp[i][j] > 1:
                    matches.append((dp[i][j], i, j))
        return matches

    def _find_files_and_dirs(self, target_dir):
        '''
        For all the files in the target_dir,
            Check:
                1. If the file is not the source file
                2. The file's extension is not in IGNORE_EXTENSIONS
            if above two conditions are not true, push the file to self.queue
        Return list of sub-directories of target_dir
        '''
        dirs = []
        try:
            for item in os.listdir(target_dir):
                # ignore hidden dir
                if item[0] != ".":
                    item_path = os.path.join(target_dir, item)
                    if os.path.isdir(item_path):
                        self.dir_count += 1
                        dirs.append(item_path)
                    elif item_path.split('.')[-1].lower() in IGNORE_EXTENSIONS:
                        self.ignored_file_count += 1
                    elif item_path != self.source_file:
                        self.file_count += 1
                        self.queue.put(item_path)
        except PermissionError:
            raise RepoSearchException(f'Permission denied. Can\'t access directory `{target_dir}`.')
        return dirs

    def _rec_traverse_repo(self, target_dir):
        '''
        Generator
        Recursively loop through the directories and push the files to self.queue
        '''
        try:
            dirs = self._find_files_and_dirs(target_dir)
            for _dir in dirs:
                # print(f'Search in: {_dir}')
                self._rec_traverse_repo(_dir)
        except RepoSearchException as err:
            print(err)

    def _worker(self, thread_id):
        while True:
            if self.queue.empty():
                time.sleep(0.001)
            file_path = self.queue.get()
            if self.stop_signal in file_path:
                # If stop signal is for this `thread_id`, than break the loop else push the signal back to queue
                if file_path == self.stop_signal + str(thread_id):
                    break
                else:
                    self.queue.put(file_path)
                continue
            curr_matches = self._find_match_in_file(file_path)
            if curr_matches:
                self.matches[file_path] = curr_matches             
                print(f'\nMatch found in {file_path}')
            for match in curr_matches:
                if match[0] == len(self.source_file_data):
                    print(f'\tFull source file matches with file {file_path} at line #{match[2] - match[0] + 1}', flush=True)
                else:
                    print(f'\tSource lines: [{match[1] - match[0] + 1}:{match[1] + 1}] matches ' +
                          f'to lines [{match[2] - match[0] + 1}:{match[2] + 1}] in {file_path}', flush=True)

    def stop_threads(self):
        for i in range(self.num_workers):
            self.queue.put(self.stop_signal + str(i))
        for i in range(self.num_workers):
            self.workers[i].join()

    def run(self):
        '''
        Starts the async loop and search
        '''
        if not os.path.isfile(self.source_file):
            raise RepoSearchException(f'Source file `{self.source_file}` doesn\'t exist.')
        if not os.path.isdir(self.repo_path):
            raise RepoSearchException(f'Directory `{self.repo_path}` doesn\'t exist.')
        with open(self.source_file, 'r', encoding="utf-8", errors='replace') as src:
            self.source_file_data = src.readlines()
            if self.source_file_data == '':
                raise RepoSearchException(f'Empty source file.')
        try:
            st = time.monotonic()
            for i in range(self.num_workers):
                self.workers.append(Thread(target=self._worker, args=(i,)))
                self.workers[i].daemon = True
                self.workers[i].start()
            print(f'Number of worker thread: {self.num_workers}. Search Started..')
            self._rec_traverse_repo(self.repo_path)
            self.stop_threads()
        except KeyboardInterrupt:
            print('Stoping threads, please wait..')
            while not self.queue.empty():
                _ = self.queue.get()
            self.stop_threads()
            return

        print()
        if not self.matches:
            print('No match found')
        else:
            print(f'Matches found in {len(self.matches.keys())} files')
        print(f'Search completed. Searched {self.dir_count} directories and ' +
              f'{self.file_count} files. Ignored {self.ignored_file_count} files')
        print(f'Ignored files with extensions: {IGNORE_EXTENSIONS}')
        print(f'Time taken to search: {round(time.monotonic()-st ,2)}sec')


if __name__ == '__main__':
    args = get_args()
    search = RepoSearch(repo_path=args.repo_path, source_file=args.source_file, num_workers=args.num_threads)
    try:
        search.run()
    except RepoSearchException as err:
        print(err)
        sys.exit(-1)
