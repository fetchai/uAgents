def cancer_classification():
    import pandas as pd
    import seaborn as sns
    import matplotlib.pyplot as plt

    dataset = pd.read_csv('data.csv')
    X = dataset.iloc[:, 2:31].values
    Y = dataset.iloc[:, 1].values

    from sklearn.preprocessing import LabelEncoder
    labelencoder_Y = LabelEncoder()
    Y = labelencoder_Y.fit_transform(Y)

    from sklearn.model_selection import train_test_split
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.25)

    from sklearn.preprocessing import StandardScaler
    sc = StandardScaler()
    X_train = sc.fit_transform(X_train)
    X_test = sc.transform(X_test)

    from sklearn.linear_model import LogisticRegression
    classifier = LogisticRegression(random_state=0)
    classifier.fit(X_train, Y_train)
    Y_pred = classifier.predict(X_test)

    from sklearn.metrics import confusion_matrix
    cm = confusion_matrix(Y_test, Y_pred)
    accuracy = (cm[0, 0] + cm[1, 1]) / (cm[0, 0] + cm[1, 1] + cm[0, 1] + cm[1, 0])

    plt.figure(figsize=(6, 4))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['Predicted No', 'Predicted Yes'], yticklabels=['Actual No', 'Actual Yes'], cbar=False)
    plt.text(0.98, 0.02, f'Accuracy: {accuracy * 100:.2f}%', fontsize=10, ha='right', va='bottom', transform=plt.gca().transAxes)
    plt.xlabel('Predicted label')
    plt.ylabel('True label')
    plt.title('Confusion Matrix')
    plt.tight_layout()
    plt.show()