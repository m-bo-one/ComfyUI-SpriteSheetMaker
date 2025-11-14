from .node import SpriteSheetFromFolder, SpriteSheetFromImages
 
NODE_CLASS_MAPPINGS = { 
    "SpriteSheetFromFolder" : SpriteSheetFromFolder,
    "SpriteSheetFromImages" : SpriteSheetFromImages,
}

NODE_DISPLAY_NAME_MAPPINGS = {
     "SpriteSheetFromFolder" : "SpriteSheet (folder)",
     "SpriteSheetFromImages" : "SpriteSheet (images)",
}
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
