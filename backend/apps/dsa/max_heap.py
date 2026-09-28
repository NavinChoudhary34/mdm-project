class MaxHeap:
    def __init__(self):
        self._items = []

    def push(self, priority, value):
        self._items.append((priority, value))
        self._sift_up(len(self._items)-1)

    def pop(self):
        if not self._items:
            return None
        top = self._items[0]
        last = self._items.pop()
        if self._items:
            self._items[0] = last
            self._sift_down(0)
        return top

    def _sift_up(self, index):
        while index > 0:
            parent = (index-1)//2
            if self._items[parent][0] >= self._items[index][0]:
                break
            self._items[parent], self._items[index] = self._items[index], self._items[parent]
            index = parent

    def _sift_down(self, index):
        size = len(self._items)
        while True:
            left = index*2+1
            right = left+1
            largest = index
            if left < size and self._items[left][0] > self._items[largest][0]:
                largest = left
            if right < size and self._items[right][0] > self._items[largest][0]:
                largest = right
            if largest == index:
                break
            self._items[index], self._items[largest] = self._items[largest], self._items[index]
            index = largest

    def __len__(self):
        return len(self._items)
