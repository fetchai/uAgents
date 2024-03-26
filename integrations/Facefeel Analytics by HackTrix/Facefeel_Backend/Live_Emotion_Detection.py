def live_emotion_detection():
    import cv2
    import numpy as np
    from keras.models import model_from_json
    from keras.preprocessing import image

    json_file_path = 'fer.json'
    weights_file_path = 'fer.h5'
    haarcascade_path = 'haarcascade_frontalface_default.xml'

    with open(json_file_path) as json_file:
        loaded_model_json = json_file.read()

    model = model_from_json(loaded_model_json)
    model.load_weights(weights_file_path)

    face_haar_cascade = cv2.CascadeClassifier(haarcascade_path)

    cap = cv2.VideoCapture(0)

    while True:
        ret, img = cap.read()
        if not ret:
            break

        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces_detected = face_haar_cascade.detectMultiScale(gray_img, 1.1, 6, minSize=(150, 150))

        for (x, y, w, h) in faces_detected:
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), thickness=2)
            roi_gray = gray_img[y:y + h, x:x + w]
            roi_gray = cv2.resize(roi_gray, (48, 48))
            img_pixels = image.img_to_array(roi_gray)
            img_pixels = np.expand_dims(img_pixels, axis=0)
            img_pixels /= 255.0

            predictions = model.predict(img_pixels)
            max_index = int(np.argmax(predictions))

            emotions = ['neutral', 'happiness', 'surprise', 'sadness', 'anger', 'disgust', 'fear']
            predicted_emotion = emotions[max_index]

            cv2.putText(img, predicted_emotion, (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)

        # Add a close button overlay in red and bold
        cv2.putText(img, 'Press Q to close', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)

        resized_img = cv2.resize(img, (1000, 700))
        cv2.imshow('Facial Emotion Recognition', resized_img)

        # Check for 'q' key press to break out of the loop
        key = cv2.waitKey(1)
        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()