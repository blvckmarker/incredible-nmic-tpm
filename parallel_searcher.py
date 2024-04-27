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

    def terminate(self):
        #self.process.join(timeout=0.1)
        print(f'Terminate {self.process.pid} process')
        self.process.terminate()
        self.in_queue.close()
        self.out_queue.close()

def init_data(data_src, ratio, cnt):
    data = pd.read_csv(data_src)['Word'].to_list()

    fast = FastSearcher(data, ratio)

    workers_cnt = cnt
    span_len = len(fast.dict) // workers_cnt
    positions = [[(i - 1) * span_len, i * span_len] for i in range(1, workers_cnt)] + [[(workers_cnt - 1) * span_len, len(fast.dict)]]

    return fast.search, positions


def init_processbag(target, cnt):
    process_bag : list[ProcessData] = []
    print("Initialize process bag")
    for i in range(cnt):
        print(f'{i + 1}/{cnt}', end='\r')
        in_queue = Queue()
        out_queue = Queue()
        process = start_new_process(target, in_queue, out_queue)
        process_bag.append(ProcessData(process, in_queue, out_queue))

    return process_bag

def find_async(word, process_bag : list[ProcessData], positions):
    cnt = len(process_bag)
    manager = Manager()
    results = manager.list()

    for i, proc in enumerate(process_bag):
        pos = positions[i]
        proc.in_queue.put([results, pos[0], pos[1], word])

    while len(results) != cnt:
        time.sleep(0.25)


    out_arr = []
    for res in results:
        out_arr.extend(res)
    
    return out_arr


# def main():
#     target, positions = init_data('./dict/russian.txt', 0.75)
#     proc_bag = init_processbag(target, len(positions))

    
#     while True:
#         inp = input("Word: ")
#         if len(inp) == 0:
#             break
        
#         print(find_async(inp, proc_bag, positions))

#     input("enter to finish proc")
#     for proc in proc_bag:
#         proc.finish()
    
#     print("end")


# if __name__ == '__main__':
#     main()