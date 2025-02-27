from .node import ImageGridNode
 
NODE_CLASS_MAPPINGS = { 
    "SpriteSheetMaker" : ImageGridNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
     "ImageGridNode" : "Image Grid"
}
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
