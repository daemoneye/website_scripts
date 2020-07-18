#!/usr/bin/env python3
import argparse
import logging
import os
from PIL import Image
import string

def arguments():
    parser = argparse.ArgumentParser(description="Code generator for https://pics.daemo.nz")
    parser.add_argument('-t', '--thumbnails',
                        dest='thumbnails',
                        action='store_true',
                        help="Regenerate all thumbnails")
    parser.add_argument('-l', '--logging',
                        dest='logit',
                        action='store_true',
                        help='Enable logging')
    return parser.parse_args()

def generate_html_page(args, image_filepath, image, html_filepath, exif, logger):
    orientation = (set_orientation(exif))
    # What exif data we want to display
    exif_info_list = ['File_Name', 'Camera_Model_Name', 'Aperture', 'ISO', 'Shutter_Speed', 'Lens_ID', 'Focal_Length', 'Shooting_Mode']
    
    HEADER = "<!DOCTYPE HTML>\n\n<html>\n<head>\n<title>" + image + "</title>\n<link rel=\"stylesheet\" href=\"../../styles.css\">\n</head>\n<body>\n"
    FOOTER = "</body>\n</html>"

    # Create HTML for each image
    IMG = "<div class=\"images\">\n<img src=\"../" + image + "\" id=\"image_canv\" class=\"rotateimg0\" width=\"100%\">\n</div>\n"
    
    # Create table for displaying data
    DATA = "<div class=\"exif\">\n<table border=\"1\">\n"
    for each in exif_info_list:
        DATA += "<tr>\n<td>"
        DATA += each.replace('_', ' ')
        if each == 'Aperture':
            DATA += "</td><td>f/"
        else:
            DATA += "</td><td>"
        DATA += exif[each]
        DATA += "</td>\n</tr>"
    DATA += "</table>\n</div>"
    
    html_file = image.split('.')[0] + ".html"
    if args.logit == True:
        logging.info("Writing %s html page", html_filepath + "/" + html_file)
    f = open(html_filepath + "/" + html_file, 'w')
    f.write(HEADER + IMG + DATA + FOOTER)
    f.close()

def generate_thumbnails(args, image_filepath, image, thumbnail_filepath, exif, logger):
    if args.thumbnails == True:
        split_image = image.split('.')
        thumbnail = split_image[0] + '_thumbnail.' + split_image[1]
        if args.logit == True:
            logging.info("Thumbnail for %s exists. Regenerating", image_filepath + "/" + image)
        generate_thumbnail(image_filepath + "/" + image, thumbnail_filepath + "/" + thumbnail, exif)
    else:
        if not os.path.exists(image_filepath+ "/" + image):
            if args.logit == True:
                logging.info("Thumbnail for %s already exists. Skipping", image_filepath + "/" + image)
            else:
                pass
        else:
            if args.logit == True:
                logging.info("Thumbnail for %s does not exist. Generating", image_filepath + "/" + image)
            split_image = image.split('.')
            thumbnail = split_image[0] + '_thumbnail.' + split_image[1]
            if args.logit == True:
                logging.info("Thumbnail for %s does not exist. Generating", thumbnail_filepath + "/" + thumbnail)
            generate_thumbnail(image_filepath + "/" + image, thumbnail_filepath + "/" + thumbnail, exif)

def generate_thumbnail(image, thumbnail, exif_data):
    im = Image.open(image)
    width, height = im.size
    MAX_SIZE = (int(width/10), int(height/10))

    im.thumbnail(MAX_SIZE)
    im = im.rotate(360 - set_orientation(exif_data), expand=True)
    im.save(thumbnail, "JPEG")

def generate_index(images_directory, exif_data, args, logger):
    HEADER = "<DOCTYPE HTML>\n\n<html>\n<head>\n<title>Daemoneye's Photos</title>\n<link rel=\"stylesheet\" href=\"styles.css\"<head>\n"
    FOOTER = "</html>"
    BODY = "<body>\n"
    # iterate through all sub directories in a given directory
    for subdir, dirs, files in os.walk(images_directory):
        # Don't look at thumbnail or html directories
        if "thumbnail" not in subdir and not subdir.endswith("html"):
            for each in os.listdir(subdir):
                if "jpg" not in each and "JPG" not in each and "thumbnails" not in each and "html" not in each and "css" not in each:
                    BODY += "<div class=\"title\">\n<h2>" + each + "</h2>\n<hr />\n</div>"
                    thumbnails = os.listdir(subdir + "/" + each + "/thumbnails")
                    html_files = os.listdir(subdir + "/" + each + "/html")
                    thumbnails.sort()
                    html_files.sort()
                    for thumb, html in zip(thumbnails, html_files):
                        BODY += "<div class=\"image\"><a href=\"/" + each + "/html/" + html + "\" /><img src=\"/" + each + "/thumbnails/" + thumb + "\" /></a><p>" + exif_data["File_Name"] + "</p></div>\n"
    BODY += "</body>"
    if args.logit == True:
        logging.info("Generating index page")
    f = open("/var/www/html/images/index.html", "w")
    f.write(HEADER + BODY + FOOTER)
    f.close()

def obtain_exif(filename):
    command = "exiftool " + str(filename)
    info = {}
    for each in os.popen(command):
        each_data = each.split(':')
        key = each_data[0].strip().replace(" ", "_")
        value = each_data[1].strip()
        info[key] = value
    return info

def set_orientation(exif_data):
    rotate = exif_data["Orientation"]
    Rotate = 0
    if "Rotate" in rotate:
        Rotate = rotate.split(' ')[1]
    return int(Rotate)

def main():
    image_filepath = "/var/www/html/images"
    args = arguments()

    # setup logging
    logging.basicConfig(filename='generate_site.log',level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    # iterate through all sub directories in a given directory
    for subdir, dirs, files in os.walk(image_filepath):
        # Don't look at thumbnail or html directories
        if "thumbnail" not in subdir and not subdir.endswith("html"):
            # list all files in the remaining directories
            for images in os.listdir(subdir):
                # concern ourselves with jpg or JPG files
                if "jpg" in images or "JPG" in images:
                    exif = obtain_exif(subdir + "/" + images)
                    generate_html_page(args, subdir, images, subdir + "/html", exif, logger)
                    generate_thumbnails(args, subdir, images, subdir + "/thumbnails", exif, logger)

    generate_index(image_filepath, exif, args, logger)

if __name__ == "__main__":
    main()
