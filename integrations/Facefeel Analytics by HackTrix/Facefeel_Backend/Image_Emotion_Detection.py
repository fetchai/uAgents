def image_emotion_detection(path):
    import cv2
    import matplotlib.pyplot as plt
    from deepface import DeepFace

    img = cv2.imread(path)
    plt.imshow(img[:, :, ::-1])

    result = DeepFace.analyze(img, actions=['emotion'], enforce_detection=False)

    detection_result = result[0]["dominant_emotion"]

    plt.text(0, -20, f"Detected Emotion: {detection_result}", color='white', fontsize=12, bbox=dict(facecolor='black', alpha=0.8))

    plt.show()