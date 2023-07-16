Unknown 3dbin packer
====
[Live web preview](https://unkown3dbinpacker.co/)


3dbin packer with bin size unknown/undefined based on [this repository](https://github.com/jerry800416/3D-bin-packing) which is based on this repository [this repository](https://github.com/enzoruiz/3dbinpacking). 



The algorithm employs a systematic approach to efficiently pack a given set of items into a single container. The process involves the following steps:

*  Calculate the total volume of all individual items combined, obtaining a theoretical volume. Based on this volume, initialize the size of the container.

*  Iterate by incrementing or decrementing the container size until all items can be successfully accommodated within it.

*  Upon determining the size at which all items fit, further decrement the container size along each axis until the limit is reached. The limit is defined as the point at which there are remaining items that cannot be fit.

*  If the initial packing attempt is successful (fullpass = True), introduce variations by altering the order of axis decrements. This is achieved by considering six possible combinations: x-y-z, x-z-y, y-x-z, y-z-x, z-x-y, and z-y-x.

*  Cache the results obtained from each combination and compare them based on the chosen criteria, such as 'volume' or 'surface'. Select the combination that yields the best result.



It is important to note that this algorithm may not perform optimally when handling a large number of items due to the repeated execution of the bin packing process during each step of incrementing or decrementing the container size. It is essentially a bruteforce method. However, it is particularly useful for tightly packing items into custom cardboard containers of specific sizes







<img src="https://github.com/KoukatsuMahoutsukai/unknown-3dbin-packer/blob/main/img/3.jpeg" width="600"/>

## OutLine
- [3D Bin Packing](#3d-bin-packing)
  - [OutLine](#outline)
  - [Improvement by jerry800416](#improvement)
  - [How to use](#how-to-use)
  - [Reference](#reference)
  - [License](#license)



## Improvement
1. **fix item float :**
    * `[fix_point = False/True] type bool` The original packaging method did not consider the gravity problem. After the packaging was completed, there were items floating in the air, which greatly reduced the space utilization of the box. I solved this problem and improved the boxing rate.

    Original packaging  |  Used fix point
    :-------------------------:|:-------------------------:
    <img src="https://github.com/KoukatsuMahoutsukai/unknown-3dbin-packer/blob/main/img/1.jpg" width="400"/>  |  <img src="https://github.com/KoukatsuMahoutsukai/unknown-3dbin-packer/blob/main/img/1.jpg" width="400"/>

2. **Item bearing problem :**
    * `[loadbear = X] type int` The original method did not consider the problem of project load-bearing, because load-bearing involves the structure, I used the priority to sort the projects with higher load-bearing capacity.The higher the number, the higher the priority.

3. **Item need to pack :**
    * `[level = X] type int` The priority can be set to sort which items should be packaged first, to ensure that these items will be packaged in bin.The lower the number, the higher the priority.

4. **Items can be placed upside down or not :**
    * `[updown = False/True] type bool` True means the item can be placed upside down.

5. **Container corner :**
    * `[corner = X] type int` Set the size of container corner, the unit is cm, color is black.

    <img src="https://github.com/KoukatsuMahoutsukai/unknown-3dbin-packer/blob/main/img/7.jpeg" width="600"/>

6. **Paint picture :** 
    * `[painter.plotBoxAndItems()]` Draw pictures.

7. **Calculate gravity distribution :**
    * `print("gravity distribution : ",bin.gravity) ` Divide the bin into four equal parts, and calculate the weight ratio of the equal parts. Ideally, the weight ratio of each equal part tends to be close.

8. **Add the order of placing items :**
    * `put_type = 0 or 1 (0 : general & 1 : open top)` Added the order of placing items. There are two placement methods. Set the bin to open top or general, and the returned results are sorted according to this method.

9. **Mixed cube and cylinder :** 
    * `typeof = cube or cylinder`  mixed with cube and cylinder .

    <img src="https://github.com/KoukatsuMahoutsukai/unknown-3dbin-packer/blob/main/img/4.jpeg" width="600"/>

10. **Check stability on item :**
    * If you want to use this function,`fix_point = True` and `check_stable=True` and `0 < support_surface_ratio <= 1 `.
    * Rule :
      1. Define a support ratio(support_surface_ratio), if the ratio below the support surface does not exceed this ratio, compare the next rule.
      2. If there is no support under any of the bottom four vertices of the item, then remove the item.

    ! check stable  |  check stable
    :-------------------------:|:-------------------------:
    <img src="https://github.com/KoukatsuMahoutsukai/unknown-3dbin-packer/blob/main/img/5.JPG" width="400"/>  |  <img src="https://github.com/KoukatsuMahoutsukai/unknown-3dbin-packer/blob/main/img/6.JPG" width="400"/>

11. **Write part number on item :**
    * Check **Painting** in [how to use](#how-to-use).
    * In order to better distinguish each item, I write part no in the middle of the item, but if I do this, it will be blocked by the color, so it is best to set the alpha value to about 0.2.

    <img src="https://github.com/KoukatsuMahoutsukai/unknown-3dbin-packer/blob/main/img/11.jpeg" width="600"/>

## How to use

**Init bin :** 
No need to init bin since the algorithm will take care of it.

**Init item :** 
```python
item1 = Item(
    partno='testItem', # partno / PN of item (unique value)
    name='wash',       # type of item
    typeof='cube',     # cube or cylinder
    WHD=(85, 60, 60),  # (width , height , depth)
    weight=10,         # item weight
    level=1,           # priority (Item need to pack)
    loadbear=100,      # item bearing
    updown=True,       # item fall down or not
    color='#FFFF37'    # set item color , you also can use color='red' or color='r'
)
```

**Init packer :**
```python
packer = Packer()          # packer init
```

**Add items to packer:**
```python
packer.addItem(item1)     # adding items to packer
```

**Start pack items :** 
```python
packer.pack(
    bigger_first=True,                 # bigger item first.
    fix_point=True,                    # fix item float problem.
    binding=[('server','cabint')],     # make a set of items.
    distribute_items=True,             # If multiple bin, to distribute or not.
    check_stable=True,                 # check stability on item.
    support_surface_ratio=0.75,        # set support surface ratio.
    number_of_decimals=0,
    fullpass=True,                     # this option explores multiple axis decrement combinations for improved packing results.
    criteria='volume'                  # choice of 'volume' or 'surface' for now. would only matter if fullpass = True
)
```

**Results :**
```python
packer.bin[i].items      # get fitted items in bin
```

**Painting :**
```python
for b in packer :
    painter = Painter(b)
    fig = painter.plotBoxAndItems(
        title=b.partno,
        alpha=0.2,         # set item alpha
        write_num=True,    # open/close write part number 
        fontsize=10        # control write_num fontsize
    )
fig.show() 
```

#### Simple example
```python
from py3dbp import Packer, Item
import time

start = time.time()

# init packing function
packer = Packer()

#  add item
packer.addItem(Item('test1', 'test','cube',(9, 8, 7), 1, 1, 100, True,'red'))
packer.addItem(Item('test2', 'test','cube',(4, 25, 1), 1, 1, 100, True,'blue'))
packer.addItem(Item('test3', 'test','cube',(2, 13, 5), 1, 1, 100, True,'gray'))
packer.addItem(Item('test4', 'test','cube',(7, 5, 4), 1, 1, 100, True,'orange'))
packer.addItem(Item('test5', 'test','cube',(10, 5, 2), 1, 1, 100, True,'lawngreen'))

# calculate packing
packer.pack(
    bigger_first=True,
    fix_point=True,
    check_stable=True,
    support_surface_ratio=0.5,
    number_of_decimals=0,
    criteria='volume',
    fullpass=True
)

# paint the results
for b in packer :
    painter = Painter(b)
    fig = painter.plotBoxAndItems(
        title=b.partno,
        alpha=0.2,         
        write_num=True,   
        fontsize=10        
    )
fig.show()
```

## Issue
* Optimizing using GA or PSO...


## Reference
* https://github.com/jerry800416/3D-bin-packing
* [Optimizing three-dimensional bin packing through simulation](https://github.com/KoukatsuMahoutsukai/unknown-3dbin-packer/blob/master/reference/OPTIMIZING%20THREE-DIMENSIONAL%20BIN%20PACKING%20THROUGH%20SIMULATION.pdf)
* https://github.com/enzoruiz/3dbinpacking
* https://github.com/nmingotti/3dbinpacking


## License

[MIT](https://github.com/KoukatsuMahoutsukai/unknown-3dbin-packer/blob/master/LICENSE)
