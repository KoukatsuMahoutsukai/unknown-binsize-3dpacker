from py3dbp import Packer, Bin, Item, Painter
import time
start = time.time()


# init packing function
packer = Packer()

packer.addItem(Item('item1', 'test', 'cube', (110, 120, 130), 1, 1, 100, True, 'red'))
packer.addItem(Item('item2', 'test', 'cube', (170, 30, 80), 1, 1, 100, True, 'blue'))
packer.addItem(Item('item3', 'test', 'cube', (40, 50, 90), 1, 1, 100, True, 'yellow'))
packer.addItem(Item('item4', 'test', 'cube', (60, 140, 120), 1, 1, 100, True, 'purple'))
packer.addItem(Item('item5', 'test', 'cube', (80, 170, 60), 1, 1, 100, True, 'brown'))
packer.addItem(Item('item6', 'test', 'cube', (90, 40, 50), 1, 1, 100, True, 'green'))
packer.addItem(Item('item7', 'test', 'cube', (100, 60, 140), 1, 1, 100, True, 'darkgreen'))
packer.addItem(Item('item8', 'test', 'cube', (30, 80, 170), 1, 1, 100, True, 'purple'))
packer.addItem(Item('item9', 'test', 'cube', (50, 90, 40), 1, 1, 100, True, 'cyan'))
packer.addItem(Item('item10', 'test', 'cube', (140, 100, 60), 1, 1, 100, True, 'pink'))
packer.addItem(Item('item11', 'test', 'cube', (70, 30, 80), 1, 1, 100, True, 'orange'))
packer.addItem(Item('item12', 'test', 'cube', (160, 50, 90), 1, 1, 100, True, 'purple'))
packer.addItem(Item('item13', 'test', 'cube', (80, 160, 120), 1, 1, 100, True, 'red'))
packer.addItem(Item('item14', 'test', 'cube', (30, 80, 170), 1, 1, 100, True, 'blue'))
packer.addItem(Item('item15', 'test', 'cube', (50, 90, 40), 1, 1, 100, True, 'green'))

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

# print result
for box in packer.bins:

    volume = box.width * box.height * box.depth
    print(":::::::::::", box.string())
    volume_t = 0
    volume_f = 0
    unfitted_name = ''

    # '''
    for item in box.items:
        print("partno : ",item.partno)
        print("type : ",item.name)
        print("color : ",item.color)
        print("position : ",item.position)
        print("rotation type : ",item.rotation_type)
        print("W*H*D : ",str(item.width) +'*'+ str(item.height) +'*'+ str(item.depth))
        print("volume : ",float(item.width) * float(item.height) * float(item.depth))
        print("weight : ",float(item.weight))
        volume_t += float(item.width) * float(item.height) * float(item.depth)
        print("***************************************************")
    print("***************************************************")
    print('space utilization : {}%'.format(round(volume_t / float(volume) * 100 ,2)))
    print('residual volumn : ', float(volume) - volume_t )
    print("gravity distribution : ",box.gravity)
    # '''
    stop = time.time()
    print('used time : ',stop - start)

    # draw results
    painter = Painter(box)
    fig = painter.plotBoxAndItems(
        title=box.partno,
        alpha=0.5,
        write_num=True,
        fontsize=10
    )
fig.show()