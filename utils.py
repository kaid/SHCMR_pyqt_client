import time

def convert_byte_size(byte_size):
    for unit in ['bytes','KB','MB','GB','TB']:
        if byte_size < 1024.0:
            return "%3.1f%s" % (byte_size, unit)
        byte_size /= 1024.0

def convert_time(seconds):
    for unit in ['秒','分钟','小时']:
        if seconds < 60:
            return "%d%s" % (seconds, unit)
        seconds /= 60

def format_time(seconds):
    return time.strftime('%H小时%M分%S秒', time.gmtime(seconds))
