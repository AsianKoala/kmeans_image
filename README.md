# kmeans_image_clustering
kmeans clustering algorithm applied to images  

### Highlights
- kmeans++ centroid initialization
- rgb bucketing
- dynamic clustering (soon)

### Usage
```py improved_generator.py [filename] [num clusters]```  

example: ```py improved_generator.py example.png 2```

### Custom generator
custom_generator.py allows the user to input rgb values for the previously calculated means  
means are mapped per pixel, meaning changed values will apply to all pixels with the old mean  
running custom_generator.py will look similar to this

![image](https://user-images.githubusercontent.com/45741682/172075946-93b6331c-65d8-44e4-aaab-fbc5682b4588.png)
