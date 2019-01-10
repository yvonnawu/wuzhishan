import queue
import types
import threading
from contextlib import contextmanager

class ObjectPool(object):
    def __init__(self, fn_cls, *args, size=1, auto_extend=True, cleanup=None, **kwargs):
        super(ObjectPool, self).__init__()
        self.fn_cls = fn_cls
        self.args = args
        self.kwargs = kwargs
        self.auto_extend = auto_extend
        self.cleanup = cleanup
        self.size = size
        self.queue = None
        self._obj_ids = set()
        self._resize(size)
        for _ in range(size):
            self._put_obj(self._get_obj())
        self._lock = threading.RLock() # use rlock to be compatible with nested contextmanager.

    def _extend(self):
        self.extend()

    def _resize(self, size):
        q = self.queue
        self._obj_ids.clear()
        self.queue = queue.Queue(maxsize=size)
        count = 0
        if q:
            while True:
                try:
                    obj = q.get_nowait()
                    self._put_obj(obj)
                    count += 1
                except queue.Empty:
                    break
        for _ in range(size - count):
            self._put_obj(self._get_obj())
        self.size = size

    def resize(self, size):
        if size == self.size:
            return
        with self._lock:
            self._resize(size)

    def extend(self):
        self.resize(self.size << 1)        
    
    def _get_obj(self):
        return self.fn_cls(*self.args, **self.kwargs)
      
    def get(self):
        # 都会返回一个对象给相关去用
        try:
            obj = self.queue.get_nowait()
        except queue.Empty:
            if self.auto_extend:
                self._extend()
                return self.get()
            else:
                return self._get_obj()
        with self._lock:
            try:
                self._obj_ids.remove(id(obj))
            except KeyError:
                pass
        return obj

    def _put_obj(self, obj):
        try:
            self.queue.put_nowait(obj)
            self._obj_ids.add(id(obj))
        except queue.Full:
            pass

    def release(self, obj):
        with self._lock:
            if id(obj) not in self._obj_ids:
                self._cleanup(obj)
                self._put_obj(obj)

    def _cleanup(self, obj):
        if self.cleanup:
            self.cleanup(obj)
        else:
            obj.__init__(*self.args, **self.kwargs)


if __name__ == "__main__":
    class Order:
        def __init__(self):
            self.volume = 0
            self.price = 0
    n = 100000
    p = ObjectPool(Order, size=n)
    objs1 = []
    for i in range(n):
        obj = p.get()
        obj.volume = 1
        objs1.append(obj)
    print(p.size)
    for i in range(n):
        obj = p.get()
    print(p.size)
    for obj in objs1:
        p.release(obj)
    print(p.size)
    for i in range(2 * n):
        obj = p.get()
        obj.volume = 2
    print(p.size)
    for obj in objs1:
        assert obj.volume == 2
