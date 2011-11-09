#!/usr/bin/env python
# encoding=utf-8

import math
import tornado.web

class Pager:
    def __init__(self, current, total, page_size = 10):
        self.total = total
        self.page_size = page_size
        self.current = current
        self.items = list()

        if (total % self.page_size) > 0:
            self.pages = int(math.floor(total / self.page_size)) + 1
        else:
            self.pages = int(math.floor(total / self.page_size))

        if self.current == 1:
            self.prev = '?page=1' 
        else:
            self.prev = '?page=%d' % (self.current - 1)

        if self.current == self.pages:
            self.next = '?page=%d' % self.pages
        else:
            self.next = '?page=%d' % (self.current + 1)

        if self.pages > 10 and self.current >= 5:
            start = self.current - 4
            stop = self.current + 5
            if stop > self.pages:
                start = self.pages - 8
                stop = self.pages + 1
        else:
            start = 1
            stop = 10
        for i in range(start, stop):
            if i <= self.pages:
                item = {'text':i, 'url':'?page=%d' % i}
                if i == self.current:
                    item['is_active'] = True
                else:
                    item['is_active'] = False
                self.items.append(item)

        if self.current == 1:
            self.offset = 0
        else:
            self.offset = self.current * self.page_size - self.page_size

class PagerModule(tornado.web.UIModule):
    def render(self, pager):
        return self.render_string('pager.html', pager=pager)
