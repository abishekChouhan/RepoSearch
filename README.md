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
