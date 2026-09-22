"""Estimate an MP3's duration from its first few KB via an HTTP range request."""
import re
import urllib.request

BITRATES = {
    (3, 3): [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320],  # MPEG1 L3
    (2, 3): [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160],  # MPEG2/2.5 L3
}
RATES = {3: [44100, 48000, 32000], 2: [22050, 24000, 16000], 0: [11025, 12000, 8000]}


def remote_duration(url, head_bytes=65536):
    req = urllib.request.Request(url, headers={'Range': f'bytes=0-{head_bytes - 1}'})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
        total = int(re.search(r'/(\d+)', r.headers['Content-Range']).group(1)) if r.headers.get('Content-Range') else len(data)
    pos = 0
    if data[:3] == b'ID3':
        size = (data[6] << 21) | (data[7] << 14) | (data[8] << 7) | data[9]
        pos = 10 + size
        if pos + 4 > len(data):
            return remote_duration(url, pos + 4096)
    while pos + 4 <= len(data):
        if data[pos] == 0xFF and (data[pos + 1] & 0xE0) == 0xE0:
            b1, b2, b3 = data[pos + 1], data[pos + 2], data[pos + 3]
            version = (b1 >> 3) & 3  # 3=MPEG1, 2=MPEG2, 0=MPEG2.5
            layer = (b1 >> 1) & 3
            br_idx, sr_idx = b2 >> 4, (b2 >> 2) & 3
            if layer == 1 and version != 1 and 0 < br_idx < 15 and sr_idx < 3:
                bitrate = BITRATES[(3 if version == 3 else 2, 3)][br_idx] * 1000
                rate = RATES[version][sr_idx]
                spf = 1152 if version == 3 else 576
                mono = (b3 >> 6) == 3
                side = (17 if mono else 32) if version == 3 else (9 if mono else 17)
                x = pos + 4 + side
                tag = data[x:x + 4]
                if tag in (b'Xing', b'Info') and data[x + 7] & 1:
                    frames = int.from_bytes(data[x + 8:x + 12], 'big')
                    return frames * spf / rate
                vbri = pos + 4 + 32
                if data[vbri:vbri + 4] == b'VBRI':
                    frames = int.from_bytes(data[vbri + 14:vbri + 18], 'big')
                    return frames * spf / rate
                return (total - pos) * 8 / bitrate
        pos += 1
    return None
