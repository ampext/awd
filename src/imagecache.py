from PySide import QtGui, QtCore
from os import listdir, path
import helper

class ImageCache():
    
    def __init__(self, path, size = 64):
        self.path = path
        self.mapping = {}    
        self.cache = {}
        self.cacheSize = size
        
        if not QtCore.QFile.exists(path):
            print("created path: {0}".format(path))
            QtCore.QDir().mkpath(path)
        
        self.Update()

    def Update(self):
        files = [f for f in listdir(self.path) if path.isfile(path.join(self.path, f))]
        
        for f in files:
            root, ext = path.splitext(f)
            if not root: continue
            
            if ext == ".png" or ext == ".jpg":
                self.mapping[root] = f
                
        if helper.debug_mode:
            print("cache updated: {0} file(s)".format(len(self.mapping)))
            
    def Touch(self, key):
        pass
    
    def Check(self, key):
        return key in self.mapping
    
    def Put(self, key, image):
        if self.Check(key): return False
        if image.isNull(): return False 
    
        image_path = self.path + QtCore.QDir.separator() + key + ".jpg"
        self.mapping[key] = image_path
    
        return image.save(image_path)
    
    def Get(self, key):
        if not self.Check(key): return None
        return QtGui.QImage(path.join(self.path, self.mapping[key]))
    
    def Clear(self):
        pass