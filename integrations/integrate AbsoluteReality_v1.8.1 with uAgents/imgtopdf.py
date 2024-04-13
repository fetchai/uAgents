import os
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def resize_image_to_fit(image, page_width, page_height):
    # Get image dimensions
    img_width, img_height = image.size
    
    # Calculate scaling factors
    width_ratio = page_width / img_width
    height_ratio = page_height / img_height
     
    # Choose the smallest ratio to fit the image within the page
    scaling_factor = min(width_ratio, height_ratio)
    
    # Resize the image
    new_width = int(img_width * scaling_factor)
    new_height = int(img_height * scaling_factor)
    return image.resize((new_width, new_height))

def convert_images_to_pdf(image_folder, text_file, pdf_path):
    # Get a list of all image files in the folder
    image_files = [f for f in os.listdir(image_folder) if f.endswith(('png', 'jpg', 'jpeg', 'gif'))]
    
    # Open the text file and read the lines
    with open(text_file, 'r') as file:
        text_lines = file.readlines()
    
    # Create a PDF canvas
    c = canvas.Canvas(pdf_path, pagesize=letter)
    page_width, page_height = letter
    
    # Loop through each image and add it to the PDF
    for i, image_file in enumerate(image_files):
        # Open and resize the image
        img_path = os.path.join(image_folder, image_file)
        img = Image.open(img_path)
        img = resize_image_to_fit(img, page_width, page_height)
        
        # Get resized image dimensions
        width, height = img.size
        
        # Add the image to the PDF
        c.drawImage(img_path, 0, page_height - height, width, height)
        
        # Add text below the image
        if i < len(text_lines):
            text = text_lines[i].strip()  # Get text from the file
            c.drawString(0, page_height - height - 20, text)
        
        # Add a new page for the next image (if any)
        c.showPage()
    
    # Save the PDF
    c.save()

