import time
from difflib import SequenceMatcher
from multiprocessing import Process, Queue
import math
import pandas as pd
import random

class FastSearcher:
    def __init__(self, dict, word, ratio) -> None:
        self.dict = dict
        self.word = word
        self.ratio = ratio

    def search(self, in_queue : Queue, out_queue : Queue) -> list[str]:
        while True:

            data = in_queue.get()
            if data is None:
                out_queue.put(None)
                out_queue.close()
                out_queue.join_thread()
                break
            
            start, end = data
            span = self.dict[start : end]

            result = []
            for w in span:
                if SequenceMatcher(None, w, self.word).ratio() >= self.ratio:
                    result.append(w)

            out_queue.put(result) 


def main():
    data = pd.read_csv('./dict/russian.txt',)['Word'].to_list()

    w = data[100]
    fast = FastSearcher(data, w, 0.75)

    t = time.time()

    workers_cnt = 20
    span_len = len(fast.dict) // workers_cnt
    positions = [[(i - 1) * span_len, i * span_len] for i in range(1, workers_cnt)] + [[(workers_cnt - 1) * span_len, len(fast.dict)]]

    in_queue = Queue()
    out_queue = Queue()

    proc = Process(target=fast.search, args=(in_queue, out_queue))
    proc.start()

    while True:
        print(w)
        inp = input()
        if len(inp) == 0:
            in_queue.put(None)
            break
        
        start, end = list(map(int, inp.split()))
        in_queue.put([start, end])
        out = out_queue.get()
        print(out)
        
    proc.join()
    in_queue.close()

    data = out_queue.get()
    out_queue.close()

    print(data)
    print(time.time() - t)

if __name__ == '__main__':
    main()