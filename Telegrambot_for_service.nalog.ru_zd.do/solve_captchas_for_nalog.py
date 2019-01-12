from collections import Counter
from keras.models import load_model
from helpers import resize_to_fit
from imutils import paths
import numpy as np
import imutils
import cv2
import pickle

def solve():
    MODEL_FILENAME = "captcha_model.hdf5"
    MODEL_LABELS_FILENAME = "model_labels.dat"
    CAPTCHA_IMAGE_FOLDER = "generated_captcha_images"
    res = {}

    # Load up the model labels (so we can translate model predictions to actual letters)
    with open(MODEL_LABELS_FILENAME, "rb") as f:
        lb = pickle.load(f)

    # Load the trained neural network
    model = load_model(MODEL_FILENAME)

    # Grab some random CAPTCHA images to test against.
    # In the real world, you'd replace this section with code to grab a real
    # CAPTCHA image from a live website.
    captcha_image_files = list(paths.list_images(CAPTCHA_IMAGE_FOLDER))
    captcha_image_files = np.random.choice(captcha_image_files, size=(50,), replace=False)

    # loop over the image paths
    for image_file in captcha_image_files:
        # Load the image and convert it to grayscale
        image = cv2.imread(image_file)
        image = cv2.resize(image, (int(600), int(400)))
        image = cv2.blur(image, (15, 15))
        image = cv2.medianBlur(image, 3)
        image = cv2.GaussianBlur(image, (5, 5), 0)
        image = cv2.bilateralFilter(image, 9, 75, 75)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Add some extra padding around the image
        image = cv2.copyMakeBorder(image, 8, 8, 8, 8, cv2.BORDER_REPLICATE)

        # threshold the image (convert it to pure black and white)
        thresh = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

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
                # Split it in half into three letter regions!
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
                half_width = int(w / 5)
                letter_image_regions.append((x, y, half_width, h))
                letter_image_regions.append((x + half_width, y, half_width, h))
                letter_image_regions.append((x + 2 * half_width, y, half_width, h))
                letter_image_regions.append((x + 3 * half_width, y, half_width , h))
                letter_image_regions.append((x + 4 * half_width, y, half_width, h))
            elif w / h >= 1.86:
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

        # If we found more or less than 6 letters in the captcha, our letter extraction
        # didn't work correcly. Skip the image instead of saving bad training data!
        if len(letter_image_regions) != 6:
            continue

        # Sort the detected letter images based on the x coordinate to make sure
        # we are processing them from left-to-right so we match the right image
        # with the right letter
        letter_image_regions = sorted(letter_image_regions, key=lambda x: x[0])

        # Create an output image and a list to hold our predicted letters
        output = cv2.merge([image] * 4)
        predictions = []
        counter = 1

        # loop over the lektters
        for letter_bounding_box in letter_image_regions:
            # Grab the coordinates of the letter in the image
            x, y, w, h = letter_bounding_box

            # Extract the letter from the original image with a 2-pixel margin around the edge
            letter_image = image[y - 2:y + h + 2, x - 2:x + w + 2]

            # Re-size the letter image to 20x20 pixels to match training data
            letter_image = resize_to_fit(letter_image, 20, 20)

            # Turn the single image into a 4d list of images to make Keras happy
            letter_image = np.expand_dims(letter_image, axis=2)
            letter_image = np.expand_dims(letter_image, axis=0)

            # Ask the neural network to make a prediction
            prediction = model.predict(letter_image)

            # Convert the one-hot-encoded prediction back to a normal letter
            letter = lb.inverse_transform(prediction)[0]
            if counter in res:
                res[counter].append(letter)
            else:
                res[counter] = [letter]
            counter += 1

            # draw the prediction on the output image
            cv2.rectangle(output, (x - 2, y - 2), (x + w + 4, y + h + 4), (0, 255, 0), 1)
            cv2.putText(output, letter, (x - 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)

        # Print the captcha's text
        # Show the annotated image
        # cv2.imshow("Output", output)
        # cv2.waitKey()
    #print(res)
    for key, value in res.items():
        most_common = Counter(value).most_common(1)
        predictions.append(most_common[0][0])
    captcha_text = "".join(predictions)
    print("CAPTCHA text is: {}".format(captcha_text))
    return captcha_text