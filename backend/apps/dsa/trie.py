class TrieNode:
    def __init__(self):
        self.children = {}
        self.movie_ids = []

class MovieTitleTrie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, title, movie_id):
        node = self.root
        for char in title.casefold():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        if movie_id not in node.movie_ids:
            node.movie_ids.append(movie_id)

    def autocomplete(self, prefix, limit=8):
        prefix = prefix.strip().casefold()
        if not prefix:
            return []
        node = self.root
        for char in prefix:
            node = node.children.get(char)
            if node is None:
                return []
        result = []
        self._collect(node, result, limit)
        return result

    def _collect(self, node, result, limit):
        if len(result) >= limit:
            return
        result.extend(node.movie_ids[:limit-len(result)])
        for char in sorted(node.children):
            self._collect(node.children[char], result, limit)
            if len(result) >= limit:
                return
