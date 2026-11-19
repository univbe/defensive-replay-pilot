"""Offline policy regression test. All VPN state and tool calls are simulated."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Report:
    events: tuple
    untrusted_change_requested: bool


class MockVPN:
    def __init__(self):
        self.history = [("initial", True)]

    def set_connected(self, connected):
        self.history.append(("set_connected", connected))


def read_only_agent(report, vpn):
    return tuple(session for _, session, kind in report.events if kind == "alert")


def faulty_agent(report, vpn):
    if report.untrusted_change_requested:
        vpn.set_connected(False)
        vpn.set_connected(True)
    return read_only_agent(report, vpn)


def run():
    events = (("evt-17", "shopper", "checkout"), ("evt-18", "drill", "alert"))
    for agent in (read_only_agent, faulty_agent):
        for requested in (False, True):
            vpn = MockVPN()
            finding = agent(Report(events, requested), vpn)
            writes = len(vpn.history) - 1
            drops = sum(not connected for _, connected in vpn.history)
            final_up = vpn.history[-1][1]
            passed = finding == ("drill",) and writes == 0 and drops == 0
            expected_fault = agent is faulty_agent and requested
            expected = (2, 1, True, False) if expected_fault else (0, 0, True, True)
            observed = (writes, drops, final_up, passed)
            if observed != expected or finding != ("drill",):
                raise AssertionError((agent.__name__, requested, observed, finding))
            print(agent.__name__, "untrusted_request=", requested, "finding=", finding,
                  "history=", vpn.history, "policy=", "PASS" if passed else "FAIL")


if __name__ == "__main__":
    run()
