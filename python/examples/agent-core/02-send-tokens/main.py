from uagents import Bureau
from alice import alice
from bob import bob

bureau = Bureau()
bureau.add(alice)
bureau.add(bob)
bureau.run()
