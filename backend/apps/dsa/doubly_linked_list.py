class Node:
    def __init__(self, value):
        self.value = value
        self.previous = None
        self.next = None

class DoublyLinkedList:
    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0

    def add_front(self, value):
        node = Node(value)
        node.next = self.head
        if self.head:
            self.head.previous = node
        else:
            self.tail = node
        self.head = node
        self.size += 1
        return node

    def remove(self, value):
        current = self.head
        while current:
            if current.value == value:
                self._unlink(current)
                return True
            current = current.next
        return False

    def remove_tail(self):
        if not self.tail:
            return None
        value = self.tail.value
        self._unlink(self.tail)
        return value

    def _unlink(self, node):
        if node.previous:
            node.previous.next = node.next
        else:
            self.head = node.next
        if node.next:
            node.next.previous = node.previous
        else:
            self.tail = node.previous
        self.size -= 1

    def values(self):
        result = []
        current = self.head
        while current:
            result.append(current.value)
            current = current.next
        return result
