from os import path as osp

cdir = osp.abspath(osp.dirname(__file__))
VERSION = open(osp.join(cdir, 'version.txt')).read().strip()
