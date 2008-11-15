# -*- coding: utf-8 -*-

def mkpyfile(path):
    file = open(path, 'w')
    file.write('# -*- coding: utf-8 -*-\n')
    file.close()