##################### Parallized using concurrent.futures
# https://docs.python.org/3/library/concurrent.futures.html
# This works very well
# Can also use SharedMemory now https://docs.python.org/3/library/multiprocessing.shared_memory.html
# NOTE: it may make sense to port this to C for parallelization if ProcessPoolExecutor is troublesome

from concurrent.futures.process import ProcessPoolExecutor
import os, signal, time, threading, sys
from tqdm import tqdm 

def start_thread_to_terminate_when_parent_process_dies(ppid):
    pid = os.getpid()
    def parent_watch():
        while True:
            try: os.kill(ppid, 0) # check if parent still alive
            except OSError: 
                print(f"PPE Process {pid} killing self because parent is not alive.")
                os.kill(pid, signal.SIGTERM) # if not, kill self
            time.sleep(1) # try every 1 second
    thread = threading.Thread(target=parent_watch, daemon=True)
    thread.start()

def start_work_ppe(workfn, items, num_workers=8, show_tqdm=False, **kwargs):
    PPE = SafePPE(num_workers=num_workers)
    res = PPE.do_work(workfn, items,show_tqdm=show_tqdm, **kwargs)
    PPE.shutdown(wait=False)
    return res

class SafePPE:
    def __init__(self, num_workers=8):
        self.num_workers = num_workers
        self.executor = ProcessPoolExecutor(max_workers=num_workers, 
                             initializer=start_thread_to_terminate_when_parent_process_dies, 
                             initargs=(os.getpid(),))
        # print("Started PPE")
        sys.stdout.flush()
    def shutdown(self, wait=True, cancel_futures=False):
        self.executor.shutdown(wait=wait, cancel_futures=cancel_futures)
    def do_work(self, workfn, items, show_tqdm=False, **kwargs):
        futures = []
        if show_tqdm:
            tqdm_bar = tqdm(total=len(items))
        for item in items:
            futures.append(self.executor.submit(workfn, item, **kwargs))
        res = []
        for future in futures:
            res.append(future.result())
            if show_tqdm:
                tqdm_bar.update(1)
        if show_tqdm:
            tqdm_bar.close()
        return res
        