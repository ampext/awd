from PySide import QtGui, QtCore
from os import listdir, path
from collections import deque
import helper

class ImageCache():
    
    def __init__(self, path, size = 32):
        self.path = path
        self.mapping = {}    
        self.cache = {}
        self.cacheQueue = deque(maxlen = size)
        
        if not QtCore.QFile.exists(path):
            print("created path: {0}".format(path))
            QtCore.QDir().mkpath(path)
        
        self.Update()

    def Update(self):        
        self.mapping.clear()
        self.cache.clear()
        self.cacheQueue.clear()
        
        files = [f for f in listdir(self.path) if path.isfile(path.join(self.path, f))]
        
        for f in files:
            root, ext = path.splitext(f)
            if not root: continue
            
            if ext == ".png" or ext == ".jpg":
                self.mapping[root] = f
                
        for key in self.mapping:
            self.Touch(key)
                
        if helper.debug_mode:
            print("cache updated: {0} file(s)".format(len(self.mapping)))
            
    def Touch(self, key):
        if self.Check(key) and key not in self.cache:
            self.cache[key] = QtGui.QImage(path.join(self.path, self.mapping[key]))
            
            if len(self.cacheQueue) == self.cacheQueue.maxlen:
                del self.cache[self.cacheQueue.popleft()]

            self.cacheQueue.append(key)
    
    def Check(self, key):
        return key in self.mapping
    
    def Put(self, key, image):
        if self.Check(key): return False
        if image.isNull(): return False 
    
        image_path = self.CreateImagePathForKey(key)
        self.mapping[key] = image_path
        
        self.Touch(key)
    
        return image.save(image_path)
    
    def Get(self, key):
        if not self.Check(key): return None
    
        self.Touch(key)
        return self.cache[key]
    
    def Clear(self):
        pass
    
    def CreateImagePathForKey(self, key):
        return self.path + QtCore.QDir.separator() + key + ".jpg"