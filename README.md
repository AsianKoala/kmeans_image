# kmeans_image_clustering
kmeans clustering algorithm applied to images  

### Highlights
- kmeans++ centroid initialization
- rgb bucketing
- dynamic clustering (soon)

### Usage
```py improved_generator.py [filename] [num clusters]```  

example: ```py improved_generator.py example.png 3```

### Custom generator
custom_generator.py allows the user to input rgb values for the previously calculated means  
means are mapped per pixel, meaning changed values will apply to all pixels with the old mean  
