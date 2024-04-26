import time
from difflib import SequenceMatcher
from multiprocessing import Process, Queue, Manager
import pandas as pd
import math

class FastSearcher:
    def __init__(self, dict, ratio) -> None:
        self.dict = dict
        self.ratio = ratio

    def search(self, in_queue : Queue, out_queue : Queue) -> list[str]:
        while True:

            data = in_queue.get()
            if data is None:
                out_queue.put(None)
                out_queue.close()
                out_queue.join_thread()
                break
        
            lst = data[0]
            word = data[3]
            start, end = data[1:3]
            span = self.dict[start : end]

            result = []
            for curr in span:
                if SequenceMatcher(None, curr, word).ratio() >= self.ratio:
                    result.append(curr)

            #out_queue.put_nowait(result) 
            lst.append(result)

def start_new_process(target, in_queue : Queue, out_queue : Queue):
    process = Process(target=target, args=(in_queue, out_queue))
    process.start()

    return process

    

class ProcessData:
    def __init__(self, process : Process, in_queue : Queue, out_queue : Queue) -> None:
        self.process = process
        self.in_queue = in_queue
        self.out_queue = out_queue

    def finish(self):
        #self.process.join(timeout=0.1)
        self.process.terminate()
        self.in_queue.close()
        self.out_queue.close()

def wait_until(cond, timeout):
    end = time.time() + timeout
    while time.time() < end:
        if cond():
            return True
        time.sleep(0.25)

    return False


def main():
    data = pd.read_csv('./dict/russian.txt',)['Word'].to_list()

    fast = FastSearcher(data, 0.75)


    workers_cnt = 10
    span_len = len(fast.dict) // workers_cnt
    positions = [[(i - 1) * span_len, i * span_len] for i in range(1, workers_cnt)] + [[(workers_cnt - 1) * span_len, len(fast.dict)]]

    process_bag : list[ProcessData] = []
    print("Initialize process bag")
    for i in range(workers_cnt):
        print(f'{i}/{workers_cnt}', end='\r')
        in_queue = Queue()
        out_queue = Queue()
        process = start_new_process(fast.search, in_queue, out_queue)
        process_bag.append(ProcessData(process, in_queue, out_queue))


    while True:
        inp = input("Word: ")
        if len(inp) == 0:
            break

        # pos pos word
        manager = Manager()
        results = manager.list()
        t = time.time()
        for i, proc in enumerate(process_bag):
            pos = positions[i]
            proc.in_queue.put([results, pos[0], pos[1], inp])

        while len(results) != workers_cnt:
            time.sleep(0.25)
            pass

        print(results)
        print(time.time() - t)


    input("enter to finish proc")
    for proc in process_bag:
        proc.finish()
    
    print("end")


if __name__ == '__main__':
    main()