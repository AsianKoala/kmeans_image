from PIL import Image
import urllib.request
import io, sys, os, random, time
import random

def check_move_count(mc):
   return [0] * len(mc) == mc

def color_dist(col1, col2):
    return sum([(col1[x] - col2[x])**2 for x in range(3)])

# uses kmeans++
def choose_means(k, img, pix, pix_dict):
    w, h = img.size
    center = pix[random.randint(0, w), random.randint(0, h)]
    centroids = [center]

    for _ in range(k-1):
        candidates = []
        weights = []
        for p in pix_dict:
            if p in centroids: continue
            deltas = []
            for c in centroids:
                deltas.append((color_dist(p, c), p))
            min_pair = min(deltas)
            candidates.append(min_pair[1])
            weights.append((min_pair[0] * 50.0) ** 2)
        chosen = random.choices(candidates, weights)[0]
        centroids.append(chosen)
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

def clustering(cb, means, count, pix_dict):
    temp_pb, temp_mc, temp_m = [[] for _ in means], [], []
    temp_cb = [0 for _ in means]
    for p in pix_dict:
        pix_dict[p][1] = mean_dist(p, means)
        temp_cb[pix_dict[p][1]] += pix_dict[p][0]
        for _ in range(pix_dict[p][0]):
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

def update_picture(img, pix, means, pix_dict):
    w,h = img.size
    means = [[int(x) for x in y] for y in means]
    for x in range(w):
        for y in range(h):
            p = pix[x,y]
            col = means[pix_dict[p][1]]
            pix[x,y] = tuple(col)

    return pix 
   
def distinct_pix_count(pix_dict):
    pairs = [(data[0], p) for p, data in pix_dict.items()]
    max_pair = max(pairs)
    return len(pix_dict), max_pair[1], max_pair[0]

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
            if valid(nx, ny, w, h) and not vis[nx][ny] and pix[nx,ny] == col:
                q.append([nx,ny])
                vis[nx][ny] = True
        for i in range(-1, 2):
            for j in range(-1, 2):
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

def get_file_name(file_path: str, k):
    if not os.path.isdir('generated'):
        os.mkdir('generated')

    file_name = None
    if '/' not in file_path:
        file_name = file_path
    else:
        file_name = file_path[file_path.rfind('/'):]

    no_ext = file_name[:file_name.find('.')]
    dir_path = './generated/' + no_ext
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)
    final_path = dir_path + '/' + no_ext + '-kmeans-' + str(k) + '.png'
    return final_path


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

    count_buckets = [0 for _ in range(k)]
    move_count = [10 for _ in range(k)]
    pix_dict = initialize_pixel_dict(img, pix)

    d_count, m_col, m_count = distinct_pix_count(pix_dict)
    print ('Distinct pixel count:', d_count)
    print ('Most common pixel:', m_col, '=>', m_count)

    means = choose_means(k, img, pix, pix_dict)
    print ('kmeans++ chosen means', means)

    count = 0
    while not check_move_count(move_count):
       count += 1
       count_buckets, move_count, means = clustering(count_buckets, means, count, pix_dict)
       if count == 1:
          print ('first means:', means)
          print ('starting sizes:', count_buckets)
    pix = update_picture(img, pix, means, pix_dict)
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
