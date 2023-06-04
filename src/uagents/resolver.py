from abc import ABC, abstractmethod
from typing import Dict, Optional
import random

from uagents.network import get_almanac_contract, get_service_contract


def query_record(agent_address: str, service: str) -> dict:
   contract = get_almanac_contract()
   query_msg = {
       "query_record": {"agent_address": agent_address, "record_type": service}
   }
   result = contract.query(query_msg)
   return result

def get_agent_address(name: str) -> str:
   query_msg = {"domain_record": {"domain": f"{name}.agent"}}
   result = get_service_contract().query(query_msg)
   if result["record"] is not None:
       registered_address = result["record"]["records"][0]["agent_address"]["records"]
       if len(registered_address) > 0:
           return registered_address[0]["address"]
       return 0
   return 1


def is_agent_address(address):
   prefix = "agent"
   expected_length = 65

   return len(address) == expected_length and address.startswith(prefix)

class Resolver(ABC):
    @abstractmethod
    async def resolve(self, address: str) -> Optional[str]:
        pass


class AlmanacResolver(Resolver):
    async def resolve(self, destination: str) -> Optional[str]:

        if is_agent_address(destination):
            address = destination
        else:
            address = get_agent_address(destination)

        result = query_record(address, "service")
        if result is not None:
            record = result.get("record") or {}
            endpoint_list = (
                record.get("record", {}).get("service", {}).get("endpoints", [])
            )

            if len(endpoint_list) > 0:
                endpoints = [val.get("url") for val in endpoint_list]
                weights = [val.get("weight") for val in endpoint_list]
                return address, random.choices(endpoints, weights=weights)[0]
        return None


class RulesBasedResolver(Resolver):
    def __init__(self, rules: Dict[str, str]):
        self._rules = rules

    async def resolve(self, address: str) -> Optional[str]:
        return self._rules.get(address)
