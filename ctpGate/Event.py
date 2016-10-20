# -*- encoding: utf-8 -*-
from Queue import Queue, Empty
import threading
import datetime


class Event(object):
    """事件类"""

    def __init__(self, eventEngine, eventName=None):
        self.name = eventName
        self.eventEngine = eventEngine
        self.__handlers = []
        self.__toSubscribe = []
        self.__toUnsubscribe = []
        self.__processing = False
    
    def subscribe(self, handler):
        if self.__processing:
            self.__toSubscribe.append(handler)
        elif handler not in self.__handlers:
            self.__addHandler(handler)
    
    def unsubscribe(self, handler):
        if self.__processing:
            self.__toUnsubscribe.append(handler)
        else:
            self.__handlers.remove(handler)

    def __applyChanges(self):
        if len(self.__toSubscribe):
            for handler in self.__toSubscribe:
                if handler not in self.__handlers:
                    self.__addHandler(handler)
            self.__toSubscribe = []
        
        if len(self.__toUnsubscribe):
            for handler in self.__toUnsubscribe:
                self.__handlers.remove(handler)
            self.__toUnsubscribe = []
    
    def process(self, *args, **kwargs):
        self.__processing = True
        # print '%s   Processing Event %s' % (datetime.datetime.now(), self.name)
        for handler in self.__handlers:
            handler(*args, **kwargs)
        self.__processing = False
        self.__applyChanges()

    def __addHandler(self, newHandler):
        """根据优先级将handler插入__handlers列表中"""
        for i, handler in enumerate(self.__handlers):
            if newHandler.priority < handler.priority:
                self.__handlers.insert(i, newHandler)
                break
        else:
            self.__handlers.append(newHandler)

    def emit(self, *args, **kwargs):
        """事件发生，将事件及对应参数放入队列"""
        self.eventEngine.put(self, args, kwargs)

    # Only for TEST purpose
    def __str__(self):
        retStr = '{0}:  '.format(self.name)
        for handler in self.__handlers:
            retStr += '{0}  '.format(handler.__dict__)
        return retStr


class EventHandler(object):
    """返回一个函数，带有优先级属性"""

    def __init__(self, func=lambda: None, priority=0):

        self._priority = priority
        self._func = func
    
    def __call__(self, *args, **kwargs):
        return self._func(*args, **kwargs)
    
    @property
    def priority(self):
        return self._priority
    

class EventEngine(object):

    def __init__(self):
        self.__queue = Queue()
        self.__active = False

        self.__thread = threading.Thread(target=self.__run)

    def __run(self):
        # i = 1
        while self.__active:
            try:
                # i += 1
                # print i
                event, args, kwargs = self.__queue.get(block=True, timeout=1)
                event.process(*args, **kwargs)
            except Empty:
                pass
    
    def start(self):
        self.__active = True
        self.__thread.start()
    
    def stop(self):
        self.__active = False

        self.__thread.join()

    def put(self, event, args, kwargs):
        self.__queue.put((event, args, kwargs))


def test():
    e1 = Event()
    def cb1():
        print('cb1')
    def cb2():
        print('cb2')
    cb1 = EventHandler(cb1)
    cb2 = EventHandler(cb2, priority=-1)

    e1.subscribe(cb1)
    e1.emit()
    e1.subscribe(cb2)
    e1.emit()


if __name__ == '__main__':
    test()
