import argparse

from .agent import check_agent
from .common import parse_agentverse_config
from .resolve import resolve


def parse_commandline() -> tuple[argparse.ArgumentParser, argparse.Namespace]:
    parser = argparse.ArgumentParser(
        description="Agentverse command line interface tools"
    )

    parser.set_defaults(op=None)
    parser.add_argument(
        "--av", required=False, type=parse_agentverse_config, help=argparse.SUPPRESS
    )
    subparser = parser.add_subparsers(help="Agentverse public operations")

    # agent-related ops
    agent = subparser.add_parser(
        "agent",
        aliases=["a"],
        help="Agent profile information and troubleshooting",
        description="Agent profile information and troubleshooting",
    )
    agent.add_argument("-a", "--address", required=True, help="Agent address")
    agent.add_argument(
        "-p",
        "--show-profile",
        required=False,
        action="store_true",
        help="Show full agent profile",
    )
    agent.add_argument(
        "-r",
        "--full-readme",
        required=False,
        action="store_true",
        help="Show full agent readme (if set)",
    )
    agent.add_argument(
        "-c",
        "--check-connectivity",
        required=False,
        action="store_true",
        help="Check registred agent endpoint connectivity ",
    )
    agent.add_argument(
        "--all", required=False, action="store_true", help="Run all checks"
    )
    agent.set_defaults(op="agent")

    # resolution-related ops
    resolve = subparser.add_parser(
        "resolve",
        aliases=["h"],
        help="Resolve agent address, handle, and domain name",
        description="Resolve agent address, handle, domain name",
    )
    resolve.add_argument(
        "identifier", help="Agent address, handle, or domain name to resolve"
    )
    resolve.set_defaults(op="resolve")

    return parser, parser.parse_args()


if __name__ == "__main__":
    parser, args = parse_commandline()

    if args.op == "agent":
        check_agent(
            args.address,
            show_profile=args.all or args.show_profile,
            full_readme=args.all or args.full_readme,
            check_connectivity=args.all or args.check_connectivity,
            agentverse=args.av,
        )
    elif args.op == "resolve":
        resolve(args.identifier, agentverse=args.av)
    else:
        parser.print_help()
