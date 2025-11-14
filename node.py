import os
import math
import numpy as np
import folder_paths
import node_helpers
from PIL import Image, ImageDraw
import torch


class SpriteSheetFromFolder:
    @classmethod
    def INPUT_TYPES(s):
        input_dir = folder_paths.get_input_directory()
        folders = [x for x in os.listdir(input_dir) if os.path.isdir(os.path.join(input_dir, x))]

        return {
            "required": { 
                "images_directory": (folders,),
                "row_count": ("INT",{"default": 2}),
                "column_count": ("INT",{"default": 2}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "main"
    CATEGORY = "SpriteSheetMaker"
 
    def get_images_from_directory(self, folder_path):
        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}
        image_files = [f for f in files if os.path.splitext(f)[1].lower() in image_extensions]
        return image_files        

    def verify_image_sizes(self, folder_path):
        image_files = self.get_images_from_directory(folder_path)

        if not image_files:
            raise ValueError("No image files found in the specified folder.")
        
        # Open the first image to use as reference
        first_image_path = os.path.join(folder_path, image_files[0])
        with Image.open(first_image_path) as first_img:
            reference_size = first_img.size
        
        # Check sizes of all images
        for filename in image_files:
            image_path = os.path.join(folder_path, filename)
            with Image.open(image_path) as img:
                current_size = img.size
                
                if current_size != reference_size:
                     raise ValueError(f"Size mismatch: {filename} has size {current_size}, expected {reference_size}")
     
    def create_image_grid(self, pil_images, grid_rows, grid_cols):
        total_tiles = grid_rows * grid_cols
        
        # Calculate total grid dimensions
        tile_width = max(img.width for img in pil_images)
        tile_height = max(img.height for img in pil_images)
        
        grid_width = tile_width * grid_cols
        grid_height = tile_height * grid_rows
        
        grid_image = Image.new('RGB', (grid_width, grid_height), color='black')
        
        # Paste images into the grid
        for i in range(grid_rows):
            for j in range(grid_cols):
                try:
                    # Calculate the position for each image
                    x = j * tile_width
                    y = i * tile_height
                    curr_image = pil_images[i * grid_cols + j]
                    
                    # Paste the image into the grid
                    # Center the image if it's smaller than the max tile size
                    paste_x = x + (tile_width - curr_image.width) // 2
                    paste_y = y + (tile_height - curr_image.height) // 2
                    grid_image.paste(curr_image, (paste_x, paste_y))
                except:
                    continue
        
        return grid_image

    def main(self, images_directory, row_count, column_count):
        images_directory = os.path.join(folder_paths.get_input_directory(), images_directory)
        self.verify_image_sizes(images_directory)

        image_files = self.get_images_from_directory(images_directory)
        pil_images = []
        for image_file in image_files:
            image_path = os.path.join(images_directory, image_file)
            pil_image = Image.open(image_path)
            pil_images.append(pil_image)

        sprite_image = self.create_image_grid(pil_images, row_count, column_count)
        sprite_image = np.array(sprite_image).astype(np.float32) / 255.0
        sprite_image = torch.from_numpy(sprite_image)[None,]
        return (sprite_image, )


class SpriteSheetFromImages:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": { 
                "image": ("IMAGE", {
                    "tooltip": "Batch of input images to assemble into a grid."
                }),
                "mode": (["auto", "manual"], {
                    "default": "auto",
                    "tooltip": "auto: grid size is calculated automatically. manual: row/column values are used."
                }),
                "filter_bad_images": (["yes", "no"], {
                    "default": "yes",
                    "tooltip": "If enabled, filters out black frames and fully transparent images."
                }),
                "row_count": ("INT", {
                    "default": 2,
                    "min": 1,
                    "tooltip": "Number of rows for the grid (used only when mode = manual)."
                }),
                "column_count": ("INT", {
                    "default": 2,
                    "min": 1,
                    "tooltip": "Number of columns for the grid (used only when mode = manual)."
                }),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "main"
    CATEGORY = "SpriteSheetMaker"

    def is_bad_image(self, pil_img):
        arr = np.asarray(pil_img)

        if arr.ndim == 3 and arr.shape[2] == 4:
            alpha = arr[:, :, 3].astype(np.float32) / 255.0
            if alpha.mean() > 0.95:
                return True

        rgb = arr[..., :3].astype(np.float32) / 255.0
        if rgb.mean() < 0.02:
            return True

        return False

    def create_image_grid(self, pil_images, grid_rows, grid_cols):
        total_tiles = grid_rows * grid_cols
        pil_images = pil_images[:total_tiles]
        tile_width = max(img.width for img in pil_images)
        tile_height = max(img.height for img in pil_images)
        grid_image = Image.new('RGB', (tile_width * grid_cols, tile_height * grid_rows), color='black')

        idx = 0
        for i in range(grid_rows):
            for j in range(grid_cols):
                if idx >= len(pil_images):
                    break
                img = pil_images[idx]
                x = j * tile_width + (tile_width - img.width) // 2
                y = i * tile_height + (tile_height - img.height) // 2
                grid_image.paste(img, (x, y))
                idx += 1

        return grid_image

    def main(self, images, mode, filter_bad_images, row_count, column_count):
        pil_images = []
        for i in range(images.shape[0]):
            img = images[i].detach().cpu().numpy()
            img = (np.clip(img, 0, 1) * 255).astype(np.uint8)

            if img.shape[2] == 3:
                pil = Image.fromarray(img, 'RGB')
            else:
                pil = Image.fromarray(img, 'RGBA')

            if filter_bad_images == "true":
                if not self.is_bad_image(pil):
                    pil_images.append(pil)
            else:
                pil_images.append(pil)

        if len(pil_images) == 0:
            raise ValueError("All images were filtered out (transparent or black).")

        batch_size = len(pil_images)

        if mode == "auto":
            column_count = math.ceil(math.sqrt(batch_size))
            row_count = math.ceil(batch_size / column_count)

        sprite_image = self.create_image_grid(pil_images, row_count, column_count)
        sprite_image = torch.from_numpy(np.array(sprite_image).astype(np.float32) / 255.0)[None, ...]

        return (sprite_image,)
