import math
import PIL
from PIL import Image, ImageTk
import urllib.request
import io, sys, os, random, time
import tkinter as tk
import shutil

def check_move_count(mc):
   return [0] * len(mc) == mc

def color_dist(col1, col2):
    return sum([(col1[x] - col2[x])**2 for x in range(3)])

# uses kmeans++
def choose_means(k, img, pix):
    w, h = img.size
    center = pix[random.randint(0, w), random.randint(0, h)]
    centroids = [center]
    for i in range(k-1):
        distances = []
        for x in range(w):
            for y in range(h):
                p = pix[x,y]
                min_dist = 1000000
                min_p = None
                for c in centroids:
                    d = color_dist(c, p)
                    if d < min_dist:
                        min_dist = d
                        min_p = p
                distances.append((min_dist, p))
        min_pair = max(distances)
        centroids.append(min_pair[1])
    return centroids

def initialize_pixel_dict(img, pix): 
    w, h = img.size
    pixel_dict = {}
    for x in range(w):
        for y in range(h):
            p = pix[x,y]
            if p not in pixel_dict:
                pixel_dict[p] = [1, -1, False]
            else:
                pixel_dict[p][0]+=1
    return pixel_dict

def mean_dist(col, means):
    min_index = -1
    min_dist = 10000000
    for i, mean in enumerate(means):
        d = color_dist(col, mean)
        if d < min_dist:
            min_dist = d
            min_index = i
    return min_index

def cant_hop(pixel, mean_query, means):
    d = color_dist(pixel, mean_query)
    min_dist = min([color_dist(mean_query, m) for m in means])
    return d < min_dist / 4


def clustering(img, pix, cb, mc, means, count, pix_dict):
   temp_pb, temp_mc, temp_m = [[] for x in means], [], []
   temp_cb = [0 for x in means]
   w,h = img.size
   for p in pix_dict:
       #if not pix_dict[p][2]:
       #    d_index = mean_dist(p, means)
       #    pix_dict[p][1] = d_index
       #    m = means[d_index]
       #    if cant_hop(p, m, means):
       #        pix_dict[p][2] = True
       pix_dict[p][1] = mean_dist(p, means)
       temp_cb[pix_dict[p][1]] += pix_dict[p][0]
       for n in range(pix_dict[p][0]):
            temp_pb[pix_dict[p][1]].append(p)
   
   for i in range(len(means)):
      if temp_cb[i] == 0:
         temp_m.append(means[i])
      else:
       sums = [sum([p[x] for p in temp_pb[i]]) for x in range(3)]
       temp_m.append([sums[x] / temp_cb[i] for x in range(3)])

   temp_mc = [ (a-b) for a, b in zip(temp_cb, cb)]
   print ('diff', count, ':', temp_mc)
   return temp_cb, temp_mc, temp_m

def update_picture(img, pix, means):
   w,h = img.size
   means = [[int(x) for x in y] for y in means]
   for x in range(w):
       for y in range(h):
           d = mean_dist(pix[x,y], means)
           p = means[d]
           pix[x,y] = tuple(p)
   return pix 
   
def distinct_pix_count(img, pix):
   cols = {}
   w, h = img.size
   for x in range(w):
       for y in range(h):
           pixel = pix[x,y]
           if pixel in cols:
               cols[pixel]+=1
           else:
               cols[pixel]=1
   max_col, max_count = pix[0, 0], 0
   for color, num in cols.items():
       if num > max_count:
           max_count = num
           max_col = color
   
   return len(cols.keys()), max_col, max_count

def valid(x, y, w, h):
    if x < 0 or y < 0: return False
    if x >= w or y >= h: return False
    return True

def bfs(x, y, vis, pix, w, h):
    q = []
    q.append([x,y])
    vis[x][y] = True
    while len(q) > 0:
        c = q.pop()
        x = c[0]
        y = c[1]
        col = pix[x,y]
        def l(nx,ny):
            if valid(nx,ny,w,h) and not vis[nx][ny] and pix[nx,ny] == col:
                q.append([nx,ny])
                vis[nx][ny] = True
        for i in range(-1,2):
            for j in range(-1,2):
                if i != x and j != y:
                    l(x+i, y+j)
    return vis

def region_counts(img, pix, means):
   region_count = [0 for _ in means]
   w,h = img.size
   visited = [[False for _ in range(h)] for _ in range(w)]
   for x in range(w):
       for y in range(h):
           if not visited[x][y]:
               p = pix[x,y]
               d = mean_dist(p, means)
               region_count[d]+=1
               visited = bfs(x, y, visited, pix, w, h)
   return region_count

def get_file_name(inp_file, k):
    name = inp_file[:inp_file.find('.')]
    path = 'generated/' + name + '/'
    ext = '.png' 
    file_name = name + '_' + 'kmeans-' + str(k) + ext
    if not os.path.exists(path):
        os.makedirs(path)
        print('created folder:', path)
    f = path + file_name
    print('outputted to', f)
    return f

def main():
   start_time = time.time()
   k = int(sys.argv[2])
   file = str(sys.argv[1]) 
   if not os.path.isfile(file):
      file = io.BytesIO(urllib.request.urlopen(file).read())
   
   img = Image.open(file)
   pix = img.load()   
   
   print ('Size:', img.size[0], 'x', img.size[1])
   print ('Pixels:', img.size[0]*img.size[1])
   d_count, m_col, m_count = distinct_pix_count(img, pix)
   print ('Distinct pixel count:', d_count)
   print ('Most common pixel:', m_col, '=>', m_count)

   count_buckets = [0 for x in range(k)]
   move_count = [10 for x in range(k)]
   means = choose_means(k, img, pix)
   print ('kmeans++ chosen means', means)
   
   pix_dict = initialize_pixel_dict(img, pix)
   
   count = 1
   while not check_move_count(move_count):
      count += 1
      count_buckets, move_count, means = clustering(img, pix, count_buckets, 
              move_count, means, count, pix_dict)
      if count == 2:
         print ('first means:', means)
         print ('starting sizes:', count_buckets)
   pix = update_picture(img, pix, means)  
   print ('Final sizes:', count_buckets)
   print ('Final means:')
   for i in range(len(means)):
      print (i+1, ':', means[i], '=>', count_buckets[i])

   #region_list = region_counts(img, pix, means)
   #print('region count:', region_list)
   
   im_name = get_file_name(file, k)
   img.save(im_name, 'PNG')  

   end_time = time.time()
   dt = end_time - start_time
   min_taken = int(dt // 60)
   sec_taken = int(dt % 60)
   print('Finished in {}m {}s'.format(min_taken, sec_taken))

   
if __name__ == '__main__': 
   main()
