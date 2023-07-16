from .constants import RotationType, Axis
from .auxiliary_methods import intersect, set2Decimal
import numpy as np

# required to plot a representation of Bin and contained items 
from matplotlib.patches import Rectangle,Circle
import matplotlib.pyplot as plt
import mpl_toolkits.mplot3d.art3d as art3d
import itertools
import logging
import matplotlib as mpl
import time
from collections import Counter
import copy
DEFAULT_NUMBER_OF_DECIMALS = 0
START_POSITION = [0, 0, 0]



class Item:

    def __init__(self, partno,name,typeof, WHD, weight, level, loadbear, updown, color):
        ''' '''
        self.partno = partno
        self.name = name
        self.typeof = typeof
        self.width = WHD[0]
        self.height = WHD[1]
        self.depth = WHD[2]
        self.weight = weight
        # Packing Priority level ,choose 1-3
        self.level = level
        # loadbear
        self.loadbear = loadbear
        # Upside down? True or False
        self.updown = updown if typeof == 'cube' else False
        # Draw item color
        self.color = color
        self.rotation_type = 0
        self.position = START_POSITION
        self.number_of_decimals = DEFAULT_NUMBER_OF_DECIMALS


    def formatNumbers(self, number_of_decimals):
        ''' '''
        self.width = set2Decimal(self.width, number_of_decimals)
        self.height = set2Decimal(self.height, number_of_decimals)
        self.depth = set2Decimal(self.depth, number_of_decimals)
        self.weight = set2Decimal(self.weight, number_of_decimals)
        self.number_of_decimals = number_of_decimals


    def string(self):
        ''' '''
        return "%s(%sx%sx%s, weight: %s) pos(%s) rt(%s) vol(%s)" % (
            self.partno, self.width, self.height, self.depth, self.weight,
            self.position, self.rotation_type, self.getVolume()
        )


    def getVolume(self):
        ''' '''
        return set2Decimal(self.width * self.height * self.depth, self.number_of_decimals)


    def getMaxArea(self):
        ''' '''
        a = sorted([self.width,self.height,self.depth],reverse=True) if self.updown == True else [self.width,self.height,self.depth]
    
        return set2Decimal(a[0] * a[1] , self.number_of_decimals)


    def getDimension(self):
        ''' rotation type '''
        if self.rotation_type == RotationType.RT_WHD:
            dimension = [self.width, self.height, self.depth]
        elif self.rotation_type == RotationType.RT_HWD:
            dimension = [self.height, self.width, self.depth]
        elif self.rotation_type == RotationType.RT_HDW:
            dimension = [self.height, self.depth, self.width]
        elif self.rotation_type == RotationType.RT_DHW:
            dimension = [self.depth, self.height, self.width]
        elif self.rotation_type == RotationType.RT_DWH:
            dimension = [self.depth, self.width, self.height]
        elif self.rotation_type == RotationType.RT_WDH:
            dimension = [self.width, self.depth, self.height]
        else:
            dimension = []

        return dimension



class Bin:

    def __init__(self, partno, WHD, max_weight,corner=0,put_type=1):
        ''' '''
        self.partno = partno
        self.width = WHD[0]
        self.height = WHD[1]
        self.depth = WHD[2]
        self.max_weight = max_weight
        self.corner = corner
        self.items = []
        self.fit_items = np.array([[0,WHD[0],0,WHD[1],0,0]])
        self.unfitted_items = []
        self.number_of_decimals = DEFAULT_NUMBER_OF_DECIMALS
        self.fix_point = False
        self.check_stable = False
        self.support_surface_ratio = 0
        self.put_type = put_type
        # used to put gravity distribution
        self.gravity = []


    def formatNumbers(self, number_of_decimals):
        ''' '''
        self.width = set2Decimal(self.width, number_of_decimals)
        self.height = set2Decimal(self.height, number_of_decimals)
        self.depth = set2Decimal(self.depth, number_of_decimals)
        self.max_weight = set2Decimal(self.max_weight, number_of_decimals)
        self.number_of_decimals = number_of_decimals


    def string(self):
        ''' '''
        return "%s(%sx%sx%s, max_weight:%s) vol(%s)" % (
            self.partno, self.width, self.height, self.depth, self.max_weight,
            self.getVolume()
        )


    def getVolume(self):
        ''' '''
        return set2Decimal(
            self.width * self.height * self.depth, self.number_of_decimals
        )


    def getTotalWeight(self):
        ''' '''
        total_weight = 0

        for item in self.items:
            total_weight += item.weight

        return set2Decimal(total_weight, self.number_of_decimals)


    def putItem(self, item, pivot,axis=None):
        ''' put item in bin '''
        fit = False
        valid_item_position = item.position
        item.position = pivot
        rotate = RotationType.ALL if item.updown == True else RotationType.Notupdown
        for i in range(0, len(rotate)):
            item.rotation_type = i
            dimension = item.getDimension()
            # rotatate
            if (
                self.width < pivot[0] + dimension[0] or
                self.height < pivot[1] + dimension[1] or
                self.depth < pivot[2] + dimension[2]
            ):
                continue

            fit = True

            for current_item_in_bin in self.items:
                if intersect(current_item_in_bin, item):
                    fit = False
                    break

            if fit:
                # cal total weight
                if self.getTotalWeight() + item.weight > self.max_weight:
                    fit = False
                    return fit
                
                # fix point float prob
                if self.fix_point == True :
                        
                    [w,h,d] = dimension
                    [x,y,z] = [float(pivot[0]),float(pivot[1]),float(pivot[2])]

                    for i in range(3):
                        # fix height
                        y = self.fixPosition([x,x+float(w),y,y+float(h),z,z+float(d)],'y')
                        # fix width
                        x = self.fixPosition([x,x+float(w),y,y+float(h),z,z+float(d)],'x')
                        # fix depth
                        z = self.fixPosition([x,x+float(w),y,y+float(h),z,z+float(d)],'z')

                    # check stability on item 
                    # rule : 
                    # 1. Define a support ratio, if the ratio below the support surface does not exceed this ratio, compare the second rule.
                    # 2. If there is no support under any vertices of the bottom of the item, then fit = False.
                    if self.check_stable == True :
                        # Cal the surface area of ​​item.
                        item_area_lower = int(dimension[0] * dimension[1])
                        # Cal the surface area of ​​the underlying support.
                        support_area_upper = 0
                        for i in self.fit_items:
                            # Verify that the lower support surface area is greater than the upper support surface area * support_surface_ratio.
                            if z == i[5]  :
                                area = len(set([ j for j in range(int(x),int(x+int(w)))]) & set([ j for j in range(int(i[0]),int(i[1]))])) * \
                                len(set([ j for j in range(int(y),int(y+int(h)))]) & set([ j for j in range(int(i[2]),int(i[3]))]))
                                support_area_upper += area

                        # If not , get four vertices of the bottom of the item.
                        if support_area_upper / item_area_lower < self.support_surface_ratio :
                            four_vertices = [[x,y],[x+float(w),y],[x,y+float(h)],[x+float(w),y+float(h)]]
                            #  If any vertices is not supported, fit = False.
                            c = [False,False,False,False]
                            for i in self.fit_items:
                                if z == i[5] :
                                    for jdx,j in enumerate(four_vertices) :
                                        if (i[0] <= j[0] <= i[1]) and (i[2] <= j[1] <= i[3]) :
                                            c[jdx] = True
                            if False in c :
                                item.position = valid_item_position
                                fit = False
                                return fit
                        
                    self.fit_items = np.append(self.fit_items,np.array([[x,x+float(w),y,y+float(h),z,z+float(d)]]),axis=0)
                    item.position = [set2Decimal(x),set2Decimal(y),set2Decimal(z)]

                if fit :
                    self.items.append(copy.deepcopy(item))

            else :
                item.position = valid_item_position

            return fit

        else :
            item.position = valid_item_position

        return fit
    
    
    def fixPosition(self, dimension, axis):
        ''' Fix item position on a specified dimension and axis '''
        if axis == 'x':
            fixed_point = [0, 1]
            unfix_point = [dimension[0], dimension[1], dimension[2], dimension[3], dimension[4], dimension[5]]
        elif axis == 'y':
            fixed_point = [2, 3]
            unfix_point = [dimension[0], dimension[1], dimension[2], dimension[3], dimension[4], dimension[5]]
        elif axis == 'z':
            fixed_point = [4, 5]
            unfix_point = [dimension[0], dimension[1], dimension[2], dimension[3], dimension[4], dimension[5]]

        fixed_set = [fixed_point]

        for j in self.fit_items:
            # Create set for the fixed dimension and axis
            fixed_bottom = set(range(int(j[fixed_point[0]]), int(j[fixed_point[1]])))
            fixed_top = set(range(int(unfix_point[fixed_point[0]]), int(unfix_point[fixed_point[1]])))

            # Create sets for the other two dimensions
            other_dim1_bottom = set(range(int(j[(fixed_point[0] + 2) % 6]), int(j[(fixed_point[1] + 2) % 6])))
            other_dim1_top = set(range(int(unfix_point[(fixed_point[0] + 2) % 6]), int(unfix_point[(fixed_point[1] + 2) % 6])))

            other_dim2_bottom = set(range(int(j[(fixed_point[0] + 4) % 6]), int(j[(fixed_point[1] + 4) % 6])))
            other_dim2_top = set(range(int(unfix_point[(fixed_point[0] + 4) % 6]), int(unfix_point[(fixed_point[1] + 4) % 6])))

            # Find intersection on the fixed dimension and both other dimensions
            if len(fixed_bottom & fixed_top) != 0 and len(other_dim1_bottom & other_dim1_top) != 0 and len(other_dim2_bottom & other_dim2_top) != 0:
                fixed_set.append([float(j[fixed_point[0]]), float(j[fixed_point[1]])])

        top_length = unfix_point[fixed_point[1]] - unfix_point[fixed_point[0]]
        fixed_set = sorted(fixed_set, key=lambda point: point[1])

        for j in range(len(fixed_set) - 1):
            if fixed_set[j + 1][0] - fixed_set[j][1] >= top_length:
                return fixed_set[j][1]

        return unfix_point[fixed_point[0]]

    def addCorner(self):
        '''add container coner '''
        if self.corner != 0 :
            corner = set2Decimal(self.corner)
            corner_list = []
            for i in range(8):
                a = Item(
                    partno='corner{}'.format(i),
                    name='corner', 
                    typeof='cube',
                    WHD=(corner,corner,corner), 
                    weight=0, 
                    level=0, 
                    loadbear=0, 
                    updown=True, 
                    color='#000000')

                corner_list.append(a)
            return corner_list


    def putCorner(self,info,item):
        '''put coner in bin '''
        fit = False
        x = set2Decimal(self.width - self.corner)
        y = set2Decimal(self.height - self.corner)
        z = set2Decimal(self.depth - self.corner)
        pos = [[0,0,0],[0,0,z],[0,y,z],[0,y,0],[x,y,0],[x,0,0],[x,0,z],[x,y,z]]
        item.position = pos[info]
        self.items.append(item)

        corner = [float(item.position[0]),float(item.position[0])+float(self.corner),float(item.position[1]),float(item.position[1])+float(self.corner),float(item.position[2]),float(item.position[2])+float(self.corner)]

        self.fit_items = np.append(self.fit_items,np.array([corner]),axis=0)
        return


    def clearBin(self):
        ''' clear item which in bin '''
        self.items = []
        self.fit_items = np.array([[0,self.width,0,self.height,0,0]])
        return


class Packer:

    def __init__(self):
        ''' '''
        self.bins = []
        self.items = []
        self.unfit_items = []
        self.total_items = 0
        # self.binding = []
        # self.apex = []


    def addBin(self, bin):
        ''' '''
        return self.bins.append(bin)


    def addItem(self, item):
        ''' '''
        self.total_items = len(self.items) + 1

        return self.items.append(item)


    def pack2Bin(self, bin, item,fix_point,check_stable,support_surface_ratio):
        ''' pack item to bin '''
        fitted = False
        bin.fix_point = fix_point
        bin.check_stable = check_stable
        bin.support_surface_ratio = support_surface_ratio

        # first put item on (0,0,0) , if corner exist ,first add corner in box. 
        if bin.corner != 0 and not bin.items:
            corner_lst = bin.addCorner()
            for i in range(len(corner_lst)) :
                bin.putCorner(i,corner_lst[i])

        elif not bin.items:
            response = bin.putItem(item, item.position)

            if not response:
                bin.unfitted_items.append(item)
            return

        for axis in range(0, 3):
            items_in_bin = bin.items
            for ib in items_in_bin:
                pivot = [0, 0, 0]
                w, h, d = ib.getDimension()
                if axis == Axis.WIDTH:
                    pivot = [ib.position[0] + w,ib.position[1],ib.position[2]]
                elif axis == Axis.HEIGHT:
                    pivot = [ib.position[0],ib.position[1] + h,ib.position[2]]
                elif axis == Axis.DEPTH:
                    pivot = [ib.position[0],ib.position[1],ib.position[2] + d]
                    
                if bin.putItem(item, pivot, axis):
                    fitted = True
                    break
            if fitted:
                break
        if not fitted:
            bin.unfitted_items.append(item)

    def putOrder(self):
        '''Arrange the order of items '''
        r = []
        for i in self.bins:
            # open top container
            if i.put_type == 2:
                i.items.sort(key=lambda item: item.position[0], reverse=False)
                i.items.sort(key=lambda item: item.position[1], reverse=False)
                i.items.sort(key=lambda item: item.position[2], reverse=False)
            # general container
            elif i.put_type == 1:
                i.items.sort(key=lambda item: item.position[1], reverse=False)
                i.items.sort(key=lambda item: item.position[2], reverse=False)
                i.items.sort(key=lambda item: item.position[0], reverse=False)
            else :
                pass
        return


    def gravityCenter(self,bin):
        ''' 
        Deviation Of Cargo gravity distribution
        ''' 
        w = int(bin.width)
        h = int(bin.height)
        d = int(bin.depth)

        area1 = [set(range(0,w//2+1)),set(range(0,h//2+1)),0]
        area2 = [set(range(w//2+1,w+1)),set(range(0,h//2+1)),0]
        area3 = [set(range(0,w//2+1)),set(range(h//2+1,h+1)),0]
        area4 = [set(range(w//2+1,w+1)),set(range(h//2+1,h+1)),0]
        area = [area1,area2,area3,area4]

        for i in bin.items:

            x_st = int(i.position[0])
            y_st = int(i.position[1])
            if i.rotation_type == 0:
                x_ed = int(i.position[0] + i.width)
                y_ed = int(i.position[1] + i.height)
            elif i.rotation_type == 1:
                x_ed = int(i.position[0] + i.height)
                y_ed = int(i.position[1] + i.width)
            elif i.rotation_type == 2:
                x_ed = int(i.position[0] + i.height)
                y_ed = int(i.position[1] + i.depth)
            elif i.rotation_type == 3:
                x_ed = int(i.position[0] + i.depth)
                y_ed = int(i.position[1] + i.height)
            elif i.rotation_type == 4:
                x_ed = int(i.position[0] + i.depth)
                y_ed = int(i.position[1] + i.width)
            elif i.rotation_type == 5:
                x_ed = int(i.position[0] + i.width)
                y_ed = int(i.position[1] + i.depth)

            x_set = set(range(x_st,int(x_ed)+1))
            y_set = set(range(y_st,y_ed+1))

            # cal gravity distribution
            for j in range(len(area)):
                if x_set.issubset(area[j][0]) and y_set.issubset(area[j][1]) : 
                    area[j][2] += int(i.weight)
                    break
                # include x and !include y
                elif x_set.issubset(area[j][0]) == True and y_set.issubset(area[j][1]) == False and len(y_set & area[j][1]) != 0 : 
                    y = len(y_set & area[j][1]) / (y_ed - y_st) * int(i.weight)
                    area[j][2] += y
                    if j >= 2 :
                        area[j-2][2] += (int(i.weight) - x)
                    else :
                        area[j+2][2] += (int(i.weight) - y)
                    break
                # include y and !include x
                elif x_set.issubset(area[j][0]) == False and y_set.issubset(area[j][1]) == True and len(x_set & area[j][0]) != 0 : 
                    x = len(x_set & area[j][0]) / (x_ed - x_st) * int(i.weight)
                    area[j][2] += x
                    if j >= 2 :
                        area[j-2][2] += (int(i.weight) - x)
                    else :
                        area[j+2][2] += (int(i.weight) - x)
                    break
                # !include x and !include y
                elif x_set.issubset(area[j][0])== False and y_set.issubset(area[j][1]) == False and len(y_set & area[j][1]) != 0  and len(x_set & area[j][0]) != 0 :
                    all = (y_ed - y_st) * (x_ed - x_st)
                    y = len(y_set & area[0][1])
                    y_2 = y_ed - y_st - y
                    x = len(x_set & area[0][0])
                    x_2 = x_ed - x_st - x
                    area[0][2] += x * y / all * int(i.weight)
                    area[1][2] += x_2 * y / all * int(i.weight)
                    area[2][2] += x * y_2 / all * int(i.weight)
                    area[3][2] += x_2 * y_2 / all * int(i.weight)
                    break
            
        r = [area[0][2],area[1][2],area[2][2],area[3][2]]
        result = []

        for i in r :
            result.append(round(i / sum(r) * 100,2))
        return result
    
    def singlepack(self, bigger_first=False,fix_point=True,check_stable=True,support_surface_ratio=0.75,number_of_decimals=DEFAULT_NUMBER_OF_DECIMALS):
        '''pack master func '''
        # set decimals
        for bin in self.bins:
            bin.formatNumbers(number_of_decimals)

        for item in self.items:
            item.formatNumbers(number_of_decimals)

        self.items.sort(key=lambda item: item.getVolume(), reverse=bigger_first)
        self.items.sort(key=lambda item: item.loadbear, reverse=True)
        self.items.sort(key=lambda item: item.level, reverse=False)

        for idx,bin in enumerate(self.bins):
            # pack item to bin
            for item in self.items:
                self.pack2Bin(bin, item, fix_point, check_stable, support_surface_ratio)

            self.bins[idx].gravity = self.gravityCenter(bin)


        # put order of items
        self.putOrder()

    def pack(self, bigger_first=False,fix_point=True,check_stable=True,support_surface_ratio=0.75,number_of_decimals=DEFAULT_NUMBER_OF_DECIMALS,criteria='volume',fullpass=False):
        
        args = (bigger_first, fix_point, check_stable, support_surface_ratio, number_of_decimals)

        theoretical_volume, steps, i, finx, finy, finz = 0, 0, 0, 0, 0, 0
        limits = ['limitx', 'limity', 'limitz']
        binslist = ['binx', 'biny', 'binz']

        # convert to the specified decimal, and sum the volume of all items to be packed to get a theoretical volume
        for item in self.items:
            item.formatNumbers(number_of_decimals)
            theoretical_volume += item.getVolume()

        # multiply by 1.3(based on empirical data) to get a closer theoretical volume to the final volume
        init_volume = round((int(theoretical_volume) * 1.3),number_of_decimals)
        # cube root the initial volume to get a initial cube as a bin
        init_dimension = round((init_volume ** (1/3)),number_of_decimals)

        vollist = []
        surfacelist = []

        # assign a lower bound to the increment or decrement so it doesnt get smaller than that and result in to more iterations
        if number_of_decimals == 0:
            lowest = 1
        else:
            lowest = round(( 0.1 ** (number_of_decimals-1)),number_of_decimals)

        # 'perm' would container a possible combination for the x,y,z axes each iteration. e.g.(x,y,z)(x,z,y)(y,x,z)...
        for perm in itertools.permutations(zip(limits, binslist)):
            if i == 1 and fullpass == False:
                break
            limitsdict = {'limitx': 0, 'limity': 0, 'limitz': 0}
            limitall, finished, overshoot = 0, 0, 0
            binx, biny, binz = init_dimension, init_dimension, init_dimension
            
            # while loop that would keep on runnning until the decrement on each axis is finished and all items is packed
            while (finished == 0):

                # if limit for the current axis is not yet reached then the increment/decrement is 5% of the dimension of that axis 
                if overshoot == 0:
                    increment = round((0.05*init_dimension),number_of_decimals)

                binx = round(binx,number_of_decimals)
                biny = round(biny,number_of_decimals)
                binz = round(binz,number_of_decimals)

                initbin = Bin('initbin', (binx, biny, binz), 999,0,0)

                if len(self.bins) == 0:
                    self.bins.append(initbin)
                else:
                    self.bins[0] = initbin

                # do a 3d bin pack based on the current bin size
                self.singlepack(*args)

                # series of decrement for each axis, the sequence of the axes to be decremented is based on the current value of 'perm'
                for idx in range(3):

                    if len(initbin.unfitted_items) == 0 and limitall == 1 and limitsdict[perm[0][0]] == 1 and limitsdict[perm[1][0]] == 1 and limitsdict[perm[2][0]] == 1:
                        
                        # assign to finx,finy,finz the current bin size if the current criteria(surface) is the smallest so far
                        if criteria == 'surface':
                            surfacearea = 2 * ((initbin.width*initbin.depth)+(initbin.height*initbin.depth)+(initbin.height*initbin.width))
                            total_surface = int(round(surfacearea, number_of_decimals))
                            if len(surfacelist) != 0 and total_surface <= min(surfacelist):
                                finx, finy, finz = initbin.width, initbin.height, initbin.depth
                            elif len(surfacelist) == 0 and fullpass == False:
                                finx, finy, finz = initbin.width, initbin.height, initbin.depth
                            surfacelist.append(total_surface)

                        # assign to finx,finy,finz the current bin size if the current criteria(volume) is the smallest so far
                        else:
                            total_vol = int(round((initbin.width * initbin.height * initbin.depth), number_of_decimals))
                            if len(vollist) != 0 and total_vol <= min(vollist):
                                finx, finy, finz = initbin.width, initbin.height, initbin.depth
                            elif len(vollist) == 0 and fullpass == False:
                                finx, finy, finz = initbin.width, initbin.height, initbin.depth
                            vollist.append(total_vol)

                        finished += 1
                        i += 1
                        break

                    if limitsdict[perm[idx][0]] == 1:
                        # if the current axis is already finished decrementing to its limit
                        continue

                    steps += 1
                    # first iteration where the binsize is still based on the theoretical volume
                    if limitall == 0:
                        if len(initbin.unfitted_items) != 0:
                            binx += increment
                            biny += increment
                            binz += increment
                            break
                        else:
                            limitall += 1

                    if limitall == 1 and limitsdict[perm[idx][0]] == 0:
                        # simply decrement the current axis by the current value of 'increment'
                        if len(initbin.unfitted_items) == 0:
                            if perm[idx][0] == 'limitx':
                                binx -= increment
                            elif perm[idx][0] == 'limity':
                                biny -= increment
                            elif perm[idx][0] == 'limitz':
                                binz -= increment
                            break

                        # if the 'increment' has halved to the point that it hit the lower bound set, decrement by the fixed value of 'lowest'
                        elif len(initbin.unfitted_items) != 0 and increment == lowest:
                            if perm[idx][0] == 'limitx':
                                binx += lowest
                            elif perm[idx][0] == 'limity':
                                biny += lowest
                            elif perm[idx][0] == 'limitz':
                                binz += lowest
                            limitsdict[perm[idx][0]] = 1
                            overshoot = 0
                            break
                        # where there are unfitted items on the bin mostly because the decrement was too large and it overshot the target/ideal bin size
                        elif len(initbin.unfitted_items) != 0:
                            if perm[idx][0] == 'limitx':
                                binx += increment
                            elif perm[idx][0] == 'limity':
                                biny += increment
                            elif perm[idx][0] == 'limitz':
                                binz += increment
                            overshoot += 1
                            # proceed to halve the 'increment'
                            if increment <= 1:
                                increment = round(increment * 0.5, number_of_decimals)
                            else:
                                increment //= 2
                            if increment < (lowest * 3):
                                increment = lowest
                            break
                    else:
                        print('error occured')

        # value of finx,finy,finz is the min(Criteria)
        initbin = Bin('initbin', (int(finx), int(finy), int(finz)), 999,0,0)
        self.bins[0] = initbin
        self.singlepack(*args)


class Painter:

    def __init__(self,bins):
        ''' '''
        self.items = bins.items
        self.width = bins.width
        self.height = bins.height
        self.depth = bins.depth


    def _plotCube(self, ax, x, y, z, dx, dy, dz, color='red',mode=2,linewidth=1,text="",fontsize=15,alpha=0.5):
        """ Auxiliary function to plot a cube. code taken somewhere from the web.  """
        xx = [x, x, x+dx, x+dx, x]
        yy = [y, y+dy, y+dy, y, y]
        
        kwargs = {'alpha': 1, 'color': color,'linewidth':linewidth }
        if mode == 1 :
            ax.plot3D(xx, yy, [z]*5, **kwargs)
            ax.plot3D(xx, yy, [z+dz]*5, **kwargs)
            ax.plot3D([x, x], [y, y], [z, z+dz], **kwargs)
            ax.plot3D([x, x], [y+dy, y+dy], [z, z+dz], **kwargs)
            ax.plot3D([x+dx, x+dx], [y+dy, y+dy], [z, z+dz], **kwargs)
            ax.plot3D([x+dx, x+dx], [y, y], [z, z+dz], **kwargs)
        else :
            p = Rectangle((x,y),dx,dy,fc=color,ec='black',alpha = alpha)
            p2 = Rectangle((x,y),dx,dy,fc=color,ec='black',alpha = alpha)
            p3 = Rectangle((y,z),dy,dz,fc=color,ec='black',alpha = alpha)
            p4 = Rectangle((y,z),dy,dz,fc=color,ec='black',alpha = alpha)
            p5 = Rectangle((x,z),dx,dz,fc=color,ec='black',alpha = alpha)
            p6 = Rectangle((x,z),dx,dz,fc=color,ec='black',alpha = alpha)
            ax.add_patch(p)
            ax.add_patch(p2)
            ax.add_patch(p3)
            ax.add_patch(p4)
            ax.add_patch(p5)
            ax.add_patch(p6)
            
            if text != "":
                ax.text( (x+ dx/2), (y+ dy/2), (z+ dz/2), str(text),color='black', fontsize=fontsize, ha='center', va='center')

            art3d.pathpatch_2d_to_3d(p, z=z, zdir="z")
            art3d.pathpatch_2d_to_3d(p2, z=z+dz, zdir="z")
            art3d.pathpatch_2d_to_3d(p3, z=x, zdir="x")
            art3d.pathpatch_2d_to_3d(p4, z=x + dx, zdir="x")
            art3d.pathpatch_2d_to_3d(p5, z=y, zdir="y")
            art3d.pathpatch_2d_to_3d(p6, z=y + dy, zdir="y")


    def _plotCylinder(self, ax, x, y, z, dx, dy, dz, color='red',mode=2,text="",fontsize=10,alpha=0.2):
        """ Auxiliary function to plot a Cylinder  """
        # plot the two circles above and below the cylinder
        p = Circle((x+dx/2,y+dy/2),radius=dx/2,color=color,alpha=0.5)
        p2 = Circle((x+dx/2,y+dy/2),radius=dx/2,color=color,alpha=0.5)
        ax.add_patch(p)
        ax.add_patch(p2)
        art3d.pathpatch_2d_to_3d(p, z=z, zdir="z")
        art3d.pathpatch_2d_to_3d(p2, z=z+dz, zdir="z")
        # plot a circle in the middle of the cylinder
        center_z = np.linspace(0, dz, 10)
        theta = np.linspace(0, 2*np.pi, 10)
        theta_grid, z_grid=np.meshgrid(theta, center_z)
        x_grid = dx / 2 * np.cos(theta_grid) + x + dx / 2
        y_grid = dy / 2 * np.sin(theta_grid) + y + dy / 2
        z_grid = z_grid + z
        ax.plot_surface(x_grid, y_grid, z_grid,shade=False,fc=color,alpha=alpha,color=color)
        if text != "" :
            ax.text( (x+ dx/2), (y+ dy/2), (z+ dz/2), str(text),color='black', fontsize=fontsize, ha='center', va='center')

    def plotBoxAndItems(self,title="",alpha=0.2,write_num=False,fontsize=10):
        """ side effective. Plot the Bin and the items it contains. """
        fig = plt.figure()
        axGlob = plt.axes(projection='3d')
        
        # plot bin 
        self._plotCube(axGlob,0, 0, 0, float(self.width), float(self.height), float(self.depth),color='black',mode=1,linewidth=2,text="")

        counter = 0
        # fit rotation type
        for item in self.items:
            rt = item.rotation_type  
            x,y,z = item.position
            [w,h,d] = item.getDimension()
            color = item.color
            text= item.partno if write_num else ""

            if item.typeof == 'cube':
                 # plot item of cube
                self._plotCube(axGlob, float(x), float(y), float(z), float(w),float(h),float(d),color=color,mode=2,text=text,fontsize=fontsize,alpha=alpha)
            elif item.typeof == 'cylinder':
                # plot item of cylinder
                self._plotCylinder(axGlob, float(x), float(y), float(z), float(w),float(h),float(d),color=color,mode=2,text=text,fontsize=fontsize,alpha=alpha)
            
            counter = counter + 1  

        
        plt.title(title)
        self.setAxesEqual(axGlob)
        return plt


    def setAxesEqual(self,ax):
        '''Make axes of 3D plot have equal scale so that spheres appear as spheres,
        cubes as cubes, etc..  This is one possible solution to Matplotlib's
        ax.set_aspect('equal') and ax.axis('equal') not working for 3D.

        Input
        ax: a matplotlib axis, e.g., as output from plt.gca().'''
        x_limits = ax.get_xlim3d()
        y_limits = ax.get_ylim3d()
        z_limits = ax.get_zlim3d()

        x_range = abs(x_limits[1] - x_limits[0])
        x_middle = np.mean(x_limits)
        y_range = abs(y_limits[1] - y_limits[0])
        y_middle = np.mean(y_limits)
        z_range = abs(z_limits[1] - z_limits[0])
        z_middle = np.mean(z_limits)

        # The plot bounding box is a sphere in the sense of the infinity
        # norm, hence I call half the max range the plot radius.
        plot_radius = 0.5 * max([x_range, y_range, z_range])

        ax.set_xlim3d([x_middle - plot_radius, x_middle + plot_radius])
        ax.set_ylim3d([y_middle - plot_radius, y_middle + plot_radius])
        ax.set_zlim3d([z_middle - plot_radius, z_middle + plot_radius])

