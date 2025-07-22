#!/usr/bin/env python
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#

import glob
import logging
import os
import sys

# import Pillow
try:
    # Pillow and PIL
    from PIL import Image, ImageDraw  # http://www.pythonware.com/products/pil/
except ImportError:
    import Image, ImageDraw  # Older namespace - http://www.pythonware.com/products/pil/

try:
    import oyaml as yaml
except ImportError:
    import yaml  # pyyaml
# TODO strictyaml - built in solution to the Norway problem...

is_win = sys.platform.startswith('win')

log = logging.getLogger('base16topng')
log.setLevel(logging.INFO)
#log.setLevel(logging.DEBUG)
disable_logging = False
#disable_logging = True
if disable_logging:
    log.setLevel(logging.NOTSET)  # only logs; WARNING, ERROR, CRITICAL

ch = logging.StreamHandler()  # use stdio

if sys.version_info >= (2, 5):
    # 2.5 added function name tracing
    logging_fmt_str = "%(process)d %(thread)d %(asctime)s - %(name)s %(filename)s:%(lineno)d %(funcName)s() - %(levelname)s - %(message)s"
else:
    if JYTHON_RUNTIME_DETECTED:
        # process is None under Jython 2.2
        logging_fmt_str = "%(thread)d %(asctime)s - %(name)s %(filename)s:%(lineno)d - %(levelname)s - %(message)s"
    else:
        logging_fmt_str = "%(process)d %(thread)d %(asctime)s - %(name)s %(filename)s:%(lineno)d - %(levelname)s - %(message)s"

formatter = logging.Formatter(logging_fmt_str)
ch.setFormatter(formatter)
log.addHandler(ch)

def parse_hex(value, hard_fail=True):
    #value = str(value)  # ensure we really have a string (variation of the the Norway problem) - TODO this is a dirty hack, this does seem to work (with Python 3.12.1) for 969896, 000001, 000000
    try:
        val = int(value, base=16)
    except TypeError:
        log.error('INVALID color %r %r' % (type(value), value))
        if hard_fail:
            raise

    r = (val & 0xFF0000) >> 16
    g = (val & 0x00FF00) >> 8
    b = (val & 0x0000FF) >> 0
    return (r, g, b)

DEFAULT_SIZE = (320, 240)
DEFAULT_SIZE = (16 * 50, 50)

def doit(base16_filename, png_filename=None, image_format='png', page_size=DEFAULT_SIZE, sanity_check_size=16):
    # if sanity_check_size is truthy, use as expected count check
    if not png_filename:
        file_name = os.path.abspath(base16_filename)
        file_name, _dummy = os.path.splitext(file_name)
        png_filename = (file_name + '.' + image_format)
    # else figure out format from file extension of base16_filename?

    # (8-bit pixels, mapped to any other mode using a color palette)
    COLOR_PALETTE_8BIT_IMAGE = 'P'  # https://pillow.readthedocs.io/en/stable/handbook/concepts.html#concept-modes

    width, height = page_size
    im = Image.new(mode=COLOR_PALETTE_8BIT_IMAGE, size=page_size, color='white')

    color_list = []
    color_dict = {}

    log.info('Opening %s', base16_filename)
    with open(base16_filename, 'r') as f:
        #theme = yaml.safe_load(f)
        theme = yaml.load(f, Loader=yaml.BaseLoader)  # resolve the Norway problem
    for k, v in theme.items():
        if 'base' not in k:
            log.debug('SKIPPING key %r', k)
            continue

        #log.debug('key %r', k)
        temp_rgb_tuple = parse_hex(v)

        if temp_rgb_tuple is None:
            log.error('key %r returns empty color key', k)
        log.debug('%s = %r - %r', k, tuple(map(hex, temp_rgb_tuple)), temp_rgb_tuple)
        if temp_rgb_tuple is not None:
            color_list.append(temp_rgb_tuple)
            color_dict[k] = temp_rgb_tuple

    log.debug('color_list = %r', color_list)
    log.debug('color_dict = %r', color_dict)
    log.info('color_list count = %d', len(color_list))
    if sanity_check_size:
        if sanity_check_size != len(color_list):
            raise NotImplementedError('Expected %d, actual color count is %d. color dict = %r' % (sanity_check_size, len(color_list), color_dict))

    log.info('Generating size %r', page_size)
    # generate vertical bars
    bar_width = int(width / len(color_list))
    bar_height = height

    offset = 0
    for color in color_list:
        ImageDraw.Draw(im).rectangle([(offset, 0), (offset + bar_width, bar_height)], fill=color)
        offset += bar_width

    log.info('Writing %s', png_filename)
    im.save(png_filename, image_format)

def main(argv=None):
    if argv is None:
        argv = sys.argv

    log.info('Python %s on %s' % (sys.version.replace('\n', ' '), sys.platform.replace('\n', ' ')))

    if is_win:
        filenames = []
        for filename_pattern in argv[1:]:
            filenames += glob.glob(filename_pattern)
    else:
        filenames = argv[1:]

    for scheme_filename in filenames:
        doit(scheme_filename)
        #doit(scheme_filename, sanity_check_size=16)
        #doit(scheme_filename, sanity_check_size=0)

    return 0


if __name__ == "__main__":
    sys.exit(main())
