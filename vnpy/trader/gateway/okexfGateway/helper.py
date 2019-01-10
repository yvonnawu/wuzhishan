import threading
import contextlib
from collections import defaultdict

from .object_pool import ObjectPool

class OrderHelper(object):
    def __init__(self):
        self._lock_pool = ObjectPool(threading.RLock, size=2000, auto_extend=True, cleanup=lambda x: None)
        self._olocks = {}
        self._orders = {}
        self._refs = {}
        self._reverse_refs = defaultdict(list)
        self._main_lock = threading.RLock()

    def insert_order(self, order_id, order, update=True):
        """Add a order to helper
        
        Parameters
        ----------
        order_id : [type]
            [description]
        order : Vnpy
            [description]
        """
        with self._main_lock:
            if order_id not in self._orders:
                lock = self._lock_pool.get()
                self._olocks[order_id] = lock
                with lock:
                    self._orders[order_id] = order
            elif update:
                self._orders[order_id] = order

    def update_order(self, order_id, order):
        with self.lock_order(order_id):
            if order_id in self._orders: # to check if it has been already removed
                self._orders[order_id] = order

    def remove_order(self, order_id, order):
        with self._main_lock:
            if order_id in self._olocks:
                lock = self._olocks.get(order_id)
                with lock:
                    del self._orders[order_id]
                    for key in self._reverse_refs.pop(order_id, []):
                        self._refs.pop(key, None)
                    self._olocks.pop(order_id, None)
                self._lock_pool.release(lock)

    def get_order(self, order_id, allow_ref=True):
        # NOTE: maybe should acquire main lock here
        if allow_ref:
            order_id = self._refs.get(order_id, order_id)
        with self.lock_order(order_id):
            return self._orders.get(order_id, None)

    def lock_order(self, order_id):
        # NOTE: maybe should acquire main lock here
        return self._olocks.get(order_id, self._main_lock)

    def bind_order(self, order_id, key):
        """Bind name reference to a exist order
        
        Parameters
        ----------
        cli_order_id : [type]
            [description]
        key : [type]
            [description]
        """
        with self.lock_order(order_id):
            if order_id in self._orders and key not in self._reverse_refs[order_id]:
                self._reverse_refs[order_id].append(key)
                self._refs[key] = order_id

    def get_order_refs(self, order_id):
        with self.lock_order(order_id):
            return self._reverse_refs.get(order_id, [])