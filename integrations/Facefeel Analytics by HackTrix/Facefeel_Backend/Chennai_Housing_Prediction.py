def chennai_housing_prediction():
    import pandas as pd
    import matplotlib.pyplot as plt

    raw_data = pd.read_csv('Chennai_housing.csv')

    raw_data = raw_data.dropna()
    x = raw_data[["INT_SQFT", "DIST_MAINROAD", "N_BEDROOM", "N_BATHROOM", "N_ROOM", "QS_ROOMS", "QS_BATHROOM", "QS_BEDROOM", "QS_OVERALL", "REG_FEE", "COMMIS"]]
    y = raw_data['SALES_PRICE']

    from sklearn.model_selection import train_test_split
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=100)

    from sklearn.linear_model import LinearRegression
    model = LinearRegression()
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)

    plt.scatter(y_test, predictions)
    plt.xlabel('Actual Sales Price')
    plt.ylabel('Predicted Sales Price')
    plt.title('Actual vs Predicted Sales Price')
    plt.show()

    from sklearn import metrics
    mse = metrics.mean_squared_error(y_test, predictions)
#    print('Mean Squared Error:', mse)
