from uagents import Bureau

from negotiation.bob import bob
from negotiation.alice import alice

bureau = Bureau()
bureau.add(alice)
bureau.add(bob)

if __name__ == '__main__':
    bureau.run()
