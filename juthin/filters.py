#!/usr/bin/env python
# encoding=utf-8

import re
from markdown import markdown
filters = []

def imgly(content):
    imgs = re.findall('(http://img.ly/[a-zA-Z0-9]+)\s?', content)
    if len(imgs) > 0:
        for img in imgs:
            img_id = re.findall('http://img.ly/[a-zA-Z0-9]+)', img)
            if (img_id[0] != 'system' and img_id[0] != 'api'):
                content.content.replace('http://img.ly/' + img_id[0], '<a href="http://img.ly/' + img_id[0] + '"></a>')
        return content
    else:
        return content
filters.append(imgly)

def clly(content):
    imgs = re.findall('(http://cl.ly/[a-zA-Z0-9]+)\s?', content)
    if (len(imgs) > 0):
        for img in imgs:
            img_id = re.findall('http://cl.ly/([a-zA-Z0-9]+)', img)
            if (img_id[0] != 'demo' and img_id[0] != 'whatever'):
                content = content.replace('http://cl.ly/' + img_id[0], '<a class="img" href="http://cl.ly/' + img_id[0] + '" target="_blank"><img style="max-width:650px;" src="http://cl.ly/' + img_id[0] + '/content" class="imgly" border="0" /></a>')
        return content
    else:
        return content
filters.append(clly)

# github gist script support
def gist(value):
    return re.sub(r'(http://gist.github.com/[\d]+)', r'<script src="\1.js"></script>', value)
filters.append(gist)

filters.append(markdown)

def apply(content):
    for filter in filters:
        content = filter(content)
    return content
