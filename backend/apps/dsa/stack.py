class Stack:
    def __init__(self):
        self._items = []

    def push(self, value):
        self._items.append(value)

    def pop(self):
        return self._items.pop() if self._items else None

    def peek(self):
        return self._items[-1] if self._items else None

    def __len__(self):
        return len(self._items)
