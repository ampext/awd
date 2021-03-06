from PySide import QtGui, QtCore
from collections import deque
import helper

class ImageCache():
    
    def __init__(self, path, size = 32):
        self.mapping = {}    
        self.cache = {}
        self.cacheQueue = deque(maxlen = size)
        self.cacheDir = QtCore.QDir(path)
        
        if not self.cacheDir.exists():
            print("created path: {0}".format(path))
            self.cacheDir.mkpath(".")
        
        self.Update()

    def Update(self):        
        self.mapping.clear()
        self.cache.clear()
        self.cacheQueue.clear()
        
        files = self.cacheDir.entryList(["*.png", "*.jpg"], QtCore.QDir.Files)
        
        for f in files:
            key = f[0:f.rfind(".")]
            if not key: continue

            self.mapping[key] = f
                
        for key in self.mapping:
            self.Touch(key)
                
        if helper.debug_mode:
            print("cache updated: {0} file(s)".format(len(self.mapping)))
            
    def Touch(self, key):
        if self.Check(key) and key not in self.cache:
            self.cache[key] = QtGui.QImage(self.cacheDir.filePath(self.mapping[key]))
            
            if len(self.cacheQueue) == self.cacheQueue.maxlen:
                del self.cache[self.cacheQueue.popleft()]

            self.cacheQueue.append(key)
    
    def Check(self, key):
        return key in self.mapping
    
    def Put(self, key, image_data, mime_type):       
        if self.Check(key): return None
        
        image = QtGui.QImage.fromData(image_data)

        if image.isNull():
            print("broken image (size : {0}, mimetype: {1})".format(len(image_data), mime_type))
            return None 
    
        image_path = self.CreateImagePathForKey(key)
        
        try:
            image_file = open(image_path, "wb+")
            image_file.write(image_data)
            image_file.close()
            
        except IOError:
            print("failed to save image on disk")
            return None
        
        self.mapping[key] = image_path
        self.Touch(key)
        
        return image
    
    def Get(self, key):
        if not self.Check(key): return None
    
        self.Touch(key)
        
        return self.cache[key]
    
    def Clear(self):       
        files = self.cacheDir.entryList(["*.png", "*.jpg"], QtCore.QDir.Files)
        
        cntr = 0
        
        for f in files:
            if self.cacheDir.remove(f): cntr = cntr + 1
            
        self.mapping.clear()
        self.cache.clear()
        self.cacheQueue.clear()
        
        if helper.debug_mode:
            print("cache cleared: {0} file(s) deleted".format(cntr))
    
    def CreateImagePathForKey(self, key):
        return self.cacheDir.filePath(key + ".jpg")