from agents.ev_charger.ev_charger import agent as ev_charger_agent
from agents.geopy_car_parking.geopy_car_parking import agent as geopy_car_parking_agent
from uagents import Bureau

if __name__ == "__main__":
    bureau = Bureau(endpoint="http://127.0.0.1:8000/submit", port=8000)
    print(f"Adding Ev charger agent to Bureau: {ev_charger_agent.address}")
    bureau.add(ev_charger_agent)
    print(
        f"Adding geopy car parking agent to Bureau: {geopy_car_parking_agent.address}"
    )
    bureau.add(geopy_car_parking_agent)
    bureau.run()
