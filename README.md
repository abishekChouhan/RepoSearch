# RepoSearch

## What it does:
Takes a [directory] git repo and a [source] file as input and search all the copies of code in source file anywhere in the git repo.

## Pre-requesites:
1. Python 3.6

## How to run:
```
cd <path-to-RepoSearch>
python search.py -repo_path <path-to-repo-dir> -source_file <source-file>
```

### To print help:
```
python search.py -h
```

### Modulerity: Import the main Class
The `RepoSearch` class in the `search.py` file can be imported in another python module.
for example:
```
from search import RepoSearch

repo_path = 'my/repo/path'
source_file = 'my/source/file.py'

search = RepoSearch(repo_path=repo_path, source_file=source_file)
search.run()
```

## How it works:
It will recursively loop through the directories inside the repository and check each file is its content is same as source file.

## Assumptions and Limitations:
1. We are searching/matching whole source file content and not line by line.
2. We are matching two conditions first with file size and then with SHA256 hash.

## Next Step
1. The functionality can be extended to search line by line using regex ('re' module)
2. Proper exception handling. The application is not tested rigorously.
3. RestAPI support can be added using FastAPI or Flask-RESTful.

## Partial matching steps:
To add the functionality of partial matching of source file, we will need to match line by line.
We will add an async function (or can also be run in other thread using Threading module), that will search for each line of source file to the current file.
If multiple continuous lines are matched, we consider that we have found a block.

## Better approach
Currently the code use asyncio, which is ok but not very optimal for our solution because our async functions are not waiting or sleeping in between. Better approach will be using Threads. Since we are doing many I/O operations (reading files), Threads are the right way to go.
Steps:
1. We will define a `worker` function which takes two arguments, first the source file content and second the path to a file from the repo. The worker will read the file and find search for line-by-line match from the source file.
2. Now we will dynamically define the number of threads to run for the worker function. Say, if the repo if large (>5000 files) we will run 12 threads and if the repo is small (<=1000 files) we will run 4 threads. (CPU's logical cores can also be taken into consideration while defining number of threads).
3. Then we will define a treads-safe Queue, that will contain the paths of files in the repo to be searched.
4. Our main function will go through the repo directory and populate the Queue with file paths.
5. Now all the running workers will consume the Queue, each worker will pop out a file path, read the file and start partial matching of the source file.
6. If we have to store the matches, we can store in a dictionary with keys as file path and values as the matched content. We will need to use mutex lock to avoid race condition.

(I will implement this solution if required)



## Updated 14th July:
1. Better approach implemented, using threads.
2. Latest code is in `search.py`. Older code (async implementation) is in `search_old.py`.
3. Line by line matching added. Used Dynamic Programming for matching.
4. Files with extensions `'zip', 'jpg', 'mp4', 'mp3', 'png', 'h5', 'csv', 'dat'` are ignored. Can be updated in code easily.
5. Now the code can find matches for block of lines (block = more than one line).
6. More than one matches is possible in single file.
7. Default value for number of worker thread is 4. Can be updated by user input

#### Empty line handling:
 1. If a matched block is followed by empty lines in both the files, the empty lines are considers as the part of matched block.
 2. Else empty lines are ignored.

#### Output Format:
Matches are printed on the screen as they are found.
Sample Output:
```
Number of worker thread: 4. Search Started..

Match found in D:\\Codes\del_me.py
        Full source file matches with file: D:\\Codes\del_me.py

Match found in D:\\Codes\some_code_file.txt
        Source lines: [9:14] matches to lines [4:9] in D:\\Codes\some_code_file.txt
        Source lines: [9:14] matches to lines [39:44] in D:\\Codes\some_code_file.txt
        Source lines: [14:17] matches to lines [25:28] in D:\\Codes\some_code_file.txt

Match found in D:\\Codes\recommender\main.py
        Source lines: [4:9] matches to lines [4:9] in D:\\Codes\recommender - Copy\main.py

Matches found in 3 files
Search completed. Searched 828 directories and 4735 files. Ignored 219 files
Ignored files with extensions: ['zip', 'jpg', 'mp4', 'mp3', 'png', 'h5', 'csv', 'dat']
Time taken to search: 105.67sec
 ```
Explanation:
The output shows that matches are found in three files :-
1. Full source file is matching with file `D:\\Codes\del_me.py`. That means content of both the files are same.
2. Three matching blocks found in file `D:\\Codes\some_code_file.txt` i.e. line #9 to line #14 of the source file is matching with line #4 to line #9 of this file and so on.
3. One matching block is find in file  `D:\\Codes\recommender\main.py`
