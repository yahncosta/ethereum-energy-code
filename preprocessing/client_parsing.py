import re
import numpy as np
import pandas as pd

_ARM_TOKENS = {"aarch64", "aarch_64", "arm64"}
_X86_TOKENS = {"x86_64", "amd64", "linux-x64", "windows-x64", "linux-386", "x86_64-unknown-linux-gnu"}

_OS_TOKENS = ["linux", "darwin", "macos", "osx", "windows", "freebsd"]

_CL_PATTERNS = [
    ("lighthouse", re.compile(r"lighthouse", re.IGNORECASE)),
    ("prysm",      re.compile(r"prysm",      re.IGNORECASE)),
    ("teku",       re.compile(r"teku",        re.IGNORECASE)),
    ("nimbus",     re.compile(r"nimbus",      re.IGNORECASE)),
    ("lodestar",   re.compile(r"lodestar",    re.IGNORECASE)),
    ("grandine",   re.compile(r"grandine",    re.IGNORECASE)),
    ("caplin",     re.compile(r"caplin",      re.IGNORECASE)),
]

_EL_PATTERNS = [
    ("geth",       re.compile(r"^geth",      re.IGNORECASE)),
    ("nethermind", re.compile(r"nethermind", re.IGNORECASE)),
    ("besu",       re.compile(r"^besu",      re.IGNORECASE)),
    ("erigon",     re.compile(r"erigon",     re.IGNORECASE)),
    ("reth",       re.compile(r"^reth",      re.IGNORECASE)),
]


def parse_clients_and_arch(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    def parse_agent(agent, patterns):
        if not agent or (isinstance(agent, float) and np.isnan(agent)):
            return None, None
        low = agent.lower()
        client = next((name for name, pat in patterns if pat.search(agent)), None)
        is_arm = any(tok in low for tok in _ARM_TOKENS)
        is_x86 = any(tok in low for tok in _X86_TOKENS)
        arch = None if (is_arm and is_x86) else ("ARM" if is_arm else ("x86" if is_x86 else None))
        return client, arch

    cl_parsed = df["AgentVersion_cl"].apply(lambda v: parse_agent(v, _CL_PATTERNS))
    el_parsed = df["AgentVersion_el"].apply(lambda v: parse_agent(v, _EL_PATTERNS))

    cl_clients, cl_arches = zip(*cl_parsed)
    el_clients, el_arches = zip(*el_parsed)

    df["consensus_client"] = list(cl_clients)
    df["execution_client"] = list(el_clients)

    def resolve_arch(c, e):
        if c == e:
            return c
        if c is None:
            return e
        if e is None:
            return c
        return None

    df["hw_arch"] = [resolve_arch(c, e) for c, e in zip(cl_arches, el_arches)]

    def detect_os(row):
        def find_tok(agent):
            if agent and not (isinstance(agent, float) and np.isnan(agent)):
                for tok in _OS_TOKENS:
                    if tok in agent.lower():
                        return tok
            return None

        cl_tok = find_tok(row["AgentVersion_cl"])
        el_tok = find_tok(row["AgentVersion_el"])

        if cl_tok is None and el_tok is None:
            return None
        if cl_tok is None:
            return el_tok
        if el_tok is None:
            return cl_tok
        if cl_tok != el_tok:
            return None
        return cl_tok

    df["os_token"] = df.apply(detect_os, axis=1)

    return df