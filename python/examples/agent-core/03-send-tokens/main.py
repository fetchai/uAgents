from alice import alice
from bob import bob
from uagents import Bureau

bureau = Bureau()
bureau.add(alice)
bureau.add(bob)
bureau.run()
