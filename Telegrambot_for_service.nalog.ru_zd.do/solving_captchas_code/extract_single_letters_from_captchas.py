import os
import os.path
import cv2
import glob
import imutils


CAPTCHA_IMAGE_FOLDER = "generated_captcha_images"
OUTPUT_FOLDER = "extracted_letter_images"


# Get a list of all the captcha images we need to process
captcha_image_files = glob.glob(os.path.join(CAPTCHA_IMAGE_FOLDER, "*"))
counts = {}

# loop over the image paths
for (i, captcha_image_file) in enumerate(captcha_image_files):
    print("[INFO] processing image {}/{}".format(i + 1, len(captcha_image_files)))

    # Since the filename contains the captcha text (i.e. "2A2X.png" has the text "2A2X"),
    # grab the base filename as the text
    filename = os.path.basename(captcha_image_file)
    captcha_correct_text = os.path.splitext(filename)[0]

    # Load the image and convert it to grayscale
    image = cv2.imread(captcha_image_file)
    image = cv2.resize(image, (int(600), int(500)))
    image = cv2.blur(image, (12, 10))
    image = cv2.medianBlur(image, 3)
    image = cv2.GaussianBlur(image, (3, 3), 0)
    image = cv2.bilateralFilter(image,9,75,75)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Add some extra padding around the image
    gray = cv2.copyMakeBorder(gray, 0, 0, 0, 0, cv2.BORDER_REPLICATE)

    # threshold the image (convert it to pure black and white)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

    # find the contours (continuous blobs of pixels) the image
    contours = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Hack for compatibility with different OpenCV versions
    contours = contours[0] if imutils.is_cv2() else contours[1]

    letter_image_regions = []

    # Now we can loop through each of the four contours and extract the letter
    # inside of each one
    for contour in contours:
        # Get the rectangle that contains the contour
        (x, y, w, h) = cv2.boundingRect(contour)

        # Compare the width and height of the contour to detect letters that
        # are conjoined into one chunk
        if w / h > 0.7 and w/h < 0.9:
            # This contour is too wide to be a single letter!
            # Split it in half into two letter regions!
            half_width = int(w / 1.8)
            letter_image_regions.append((x, y, half_width, h))
            letter_image_regions.append((x + half_width, y, half_width, h))
        elif w / h >= 0.9 and w / h < 1.3:
            # Split it in half into four letter regions!
            half_width = int(w / 3)
            letter_image_regions.append((x, y, half_width, h))
            letter_image_regions.append((x + half_width, y, half_width, h))
            letter_image_regions.append((x + 2 * half_width, y, half_width, h))
        elif w / h >= 1.3 and w / h < 1.6:
            # Split it in half into four letter regions!
            half_width = int(w / 4)
            letter_image_regions.append((x, y, half_width, h))
            letter_image_regions.append((x + half_width, y, half_width, h))
            letter_image_regions.append((x + 2 * half_width, y, half_width, h))
            letter_image_regions.append((x + 3 * half_width, y, half_width , h))
        elif w / h >= 1.6 and w / h < 1.86:
            # Split it in half into five letter regions!
            half_width = int(w / 5)
            letter_image_regions.append((x, y, half_width, h))
            letter_image_regions.append((x + half_width, y, half_width, h))
            letter_image_regions.append((x + 2 * half_width, y, half_width, h))
            letter_image_regions.append((x + 3 * half_width, y, half_width , h))
            letter_image_regions.append((x + 4 * half_width, y, half_width, h))
        elif w / h >= 1.86:
            # Split it in half into six letter regions!
            half_width = int(w / 6)
            letter_image_regions.append((x, y, half_width, h))
            letter_image_regions.append((x + half_width, y, half_width, h))
            letter_image_regions.append((x + 2 * half_width, y, half_width, h))
            letter_image_regions.append((x + 3 * half_width, y, half_width , h))
            letter_image_regions.append((x + 4 * half_width, y, half_width, h))
            letter_image_regions.append((x + 5 * half_width, y, half_width, h))
        else:
            # This is a normal letter by itself
            letter_image_regions.append((x, y, w, h))
        # letter_image_regions.append((x, y, w, h))
    # # If we found more or less than 6 letters in the captcha, our letter extraction
    # # didn't work correcly. Skip the image instead of saving bad training data!
    print(len(letter_image_regions))
    # if len(letter_image_regions) != 4:
    #     continue
    # print(captcha_image_file)
    # Sort the detected letter images based on the x coordinate to make sure
    # we are processing them from left-to-right so we match the right image
    # with the right letter
    letter_image_regions = sorted(letter_image_regions, key=lambda x: x[0])

    # Save out each letter as a single image
    for letter_bounding_box, letter_text in zip(letter_image_regions, captcha_correct_text):
        # Grab the coordinates of the letter in the image
        x, y, w, h = letter_bounding_box

        # Extract the letter from the original image with a 5-pixel margin around the edge
        letter_image = image[y - 5:y + h + 5, x - 5:x + w + 10]

        # Get the folder to save the image in
        save_path = os.path.join(OUTPUT_FOLDER, letter_text)

        # if the output directory does not exist, create it
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        # write the letter image to a file
        count = counts.get(letter_text, 1)
        p = os.path.join(save_path, "{}.png".format(str(count).zfill(6)))
        cv2.imwrite(p, letter_image)

        # increment the count for the current key
        counts[letter_text] = count + 1