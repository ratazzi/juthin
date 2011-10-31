import re

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
