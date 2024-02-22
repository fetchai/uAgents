# 🚗 uAgent Mobility Integrations Examples 🚴

This repository contains examples of mobility integrations using two agents: `ev_charger` and `geoapi_car_parking`.

1. `ev_charger`: This agent takes latitude, longitude, and a miles radius as input and returns available EV chargers in that region within the given radius. It utilizes the [OpenChargeMap](https://openchargemap.org/site/develop/api) API to retrieve the desired results.

2. `geoapi_car_parking`: This agent takes latitude, longitude, and a miles radius as input and returns available parking spaces within that radius. The agent leverages [Geoapify](https://www.geoapify.com/) to fetch the desired results.

## Getting Started 🚀

To use these agents, follow the steps below:

### Step 1: Obtain API Keys 🔑

Before running the agents, you need to obtain the required API keys:

#### OPENCHARGEMAP_API_KEY 🔌

1. Visit the OpenChargeMap API website: https://openchargemap.org/site/develop/api.
2. If you don't have an account, create one by signing up.
3. Once you are logged in, click on the MY PROFILE > my apps at the top.
4. Click on REGISTER AN APPLICATION button.
5. Fill out the required information in the form, including the purpose of using the API, and submit the request.
6. Once approved, you will see your `OPENCHARGEMAP_API_KEY` under MY API KEYS.

#### GEOAPI_API_KEY 🗺️

1. Go to the Geoapify website: https://www.geoapify.com/.
2. Sign in to your Google account or create a new one if you don't have an existing account.
3. Once you are logged in, create a new project by clicking on the "Add a new project" button under the Projects section.
4. Give your project a name and click "OK" to create the new project.
5. Your `GEOAPI_API_KEY` will be generated. Copy this key and keep it secure, as it will be used to access Geoapify Projects and other services.

#### GOOGLE_MAPS_API_KEY 🗺️

1. Go to the Google Cloud Console: https://console.cloud.google.com/.
2. Create a new project or select an existing project from the top right corner.
3. In the left navigation, click on the "API & Services" > "Credentials" section.
4. Create a new API Key and restrict it to the Google Maps APIs you plan to use (e.g., Maps JavaScript API).
5. Copy your `GOOGLE_MAPS_API_KEY` and make sure to keep it secure.