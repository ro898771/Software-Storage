from PySide6.QtGui import QIcon

class IconManager:
    def __init__(self):
        # 1. Centralize the base path here. 
        # If the resource prefix changes, you only edit this one line.
        self.base = ":/newPrefix/images/"

    def _get(self, filename):
        """Helper to join path and create QIcon"""
        return QIcon(f"{self.base}{filename}")

    # 2. Define Properties for each icon
    # Using @property allows lazy loading (only loads when you ask for it)
    # OR just standard attributes if you prefer. Here is the cleanest way:

    @property
    def Load(self):      return self._get("load.png")
    
    @property
    def Param(self):     return self._get("2820296.png") # Mapped cryptic name to readable name
    
    @property
    def Plotting(self):  return self._get("Plot.png")
    
    @property
    def List(self):      return self._get("files.png")
    
    @property
    def LotList(self):   return self._get("FileLot.png")
    
    @property
    def Replace(self):   return self._get("change.png")
    
    @property
    def PPT(self):       return self._get("ppt.jpg")
    
    @property
    def Capture(self):   return self._get("image.jpg")
    
    @property
    def Service(self):   return self._get("speed.png")
    
    @property
    def Reset(self):     return self._get("reset.png")
    
    @property
    def Update(self):    return self._get("exclaimation.png")
    
    @property
    def Window(self):    return self._get("ploticon.png")
    
    @property
    def Setting(self):   return self._get("setting.png")
    
    @property
    def Line(self):      return self._get("S.png")
    
    @property
    def Undo(self):      return self._get("Brush.png")
    
    @property
    def Gen(self):       return self._get("checkSave.png")
    
    @property
    def Edit(self):      return self._get("Select.png")
    
    @property
    def Execute(self):   return self._get("Quick.png")
    
    @property
    def Plus(self):      return self._get("plus.png")
    
    @property
    def Tick(self):      return self._get("tick.png")
    
    @property
    def RegexList(self): return self._get("ticker.png")
    
    @property
    def Select(self):    return self._get("Selection.png")

    @property
    def reverse(self):    return self._get("undo.png")

    @property
    def reverse2(self):    return self._get("reverse.png")

