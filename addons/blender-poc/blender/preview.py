"""確認用: シートの一部のセルを並べて拡大した画像を work/preview.png に出す。"""
import os, bpy, numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def load(p):
    im = bpy.data.images.load(p, check_existing=False); w, h = im.size
    a = np.empty(w*h*4, np.float32); im.pixels.foreach_get(a); bpy.data.images.remove(im)
    return np.flipud(a.reshape(h, w, 4))
t = load(os.path.join(ROOT, "src/track.png")); b = load(os.path.join(ROOT, "src/tollbooth.png"))
crop = lambda s, r, c, y0=64, y1=192: s[r*256+y0:r*256+y1, c*256+48:c*256+208]
tiles = [crop(t,0,2), crop(t,1,0), crop(t,1,5,40,192), crop(t,0,5), crop(t,2,5), crop(t,3,5), crop(b,0,0,32,240), crop(b,0,1,32,240)]
h = max(x.shape[0] for x in tiles)
tiles = [np.pad(x, ((0, h-x.shape[0]), (0, 4), (0, 0)), constant_values=1) for x in tiles]
row = np.concatenate(tiles, 1).repeat(3, 0).repeat(3, 1)
im = bpy.data.images.new("p", row.shape[1], row.shape[0]); im.pixels.foreach_set(np.flipud(row).ravel())
im.filepath_raw = os.path.join(ROOT, "work/preview.png"); im.file_format = "PNG"; im.save()
