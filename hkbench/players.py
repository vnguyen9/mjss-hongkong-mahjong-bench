"""Players: the things that sit at a seat and answer ``decide`` messages.

``LocalPlayer`` runs a reference bot inside this process. ``ProcessPlayer`` runs any program that
speaks the JSON-lines protocol (``protocol/PROTOCOL.md``). Both are handed the same message and
both must answer with one legal action id.

When an answer is late, malformed, or not legal, the bench plays a fallback action for that seat
and records a fault. A crash or a broken protocol stops the run.
"""

from __future__ import annotations

import json
import os
import queue
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from hkbench.agents.registry import REFERENCE_BOTS
from hkbench.view import PROTOCOL, SeatView

DEFAULT_DECISION_TIMEOUT_S = 10.0
DEFAULT_HANDSHAKE_TIMEOUT_S = 30.0

#: The only variables a bot's process inherits. Nothing of the bench's own (``HKBENCH_*``, the private
#: deck's path) is among them. ``LC_*`` is let through as a prefix. Anything else a bot needs is asked for
#: by name with ``--bot-env``.
BOT_ENV_ALLOW = ("PATH", "HOME", "LANG", "TMPDIR", "TEMP", "TMP", "SYSTEMROOT")
BOT_ENV_PREFIXES = ("LC_",)
BOT_ENV_FORBIDDEN_PREFIX = "HKBENCH_"


#: Variables that name a place a program writes. Each bot process gets its own empty directory for all of them.
BOT_SCRATCH_VARS = ("HOME", "TMPDIR", "TEMP", "TMP")

#: How long a bot gets to leave after ``bye`` before its whole process group is killed.
BYE_GRACE_S = 1.0


def bot_environment(source: Optional[Dict[str, str]] = None, extra: Optional[Dict[str, str]] = None,
                    scratch: Optional[str] = None) -> Dict[str, str]:
    """The environment a bot's process starts with: the allowlist taken from ``source``, plus ``extra``.

    ``scratch`` is the bot's own empty directory: ``HOME``, ``TMPDIR``, ``TEMP`` and ``TMP`` point at it.
    ``extra`` is what the run was explicitly asked to hand over. It may not name an ``HKBENCH_*``
    variable: those belong to the bench.
    """
    src = os.environ if source is None else source
    env = {k: v for k, v in src.items()
           if k.upper() in BOT_ENV_ALLOW or k.upper().startswith(BOT_ENV_PREFIXES)}
    if scratch is not None:
        for k in BOT_SCRATCH_VARS:
            env[k] = scratch
    for k, v in (extra or {}).items():
        if k.upper().startswith(BOT_ENV_FORBIDDEN_PREFIX):
            raise ValueError("a bot may not be given %s: %s* variables belong to the bench" % (k, BOT_ENV_FORBIDDEN_PREFIX))
        env[k] = v
    return env


class BotCrashed(RuntimeError):
    """The bot's process ended, or spoke so badly the run cannot continue."""


def fallback_action(msg: Dict[str, Any]) -> int:
    """What the bench plays for a seat whose bot gave no usable answer.

    On a claim: pass. On your own turn: throw the tile you just drew, or if that is not
    possible the lowest-numbered legal discard.
    """
    legal = [a["id"] for a in msg["legal"]]
    if msg["phase"] == "claim":
        return 0 if 0 in legal else legal[0]
    drawn = msg["you"]["drawn"]
    if drawn is not None and (2 + drawn) in legal:
        return 2 + drawn
    discards = [a for a in legal if 2 <= a <= 35]
    return discards[0] if discards else legal[0]


class Player:
    name = "player"

    def decide(self, msg: Dict[str, Any]) -> Tuple[int, Optional[str]]:
        """Return (action id, fault). ``fault`` is None when the answer was legal and on time."""
        raise NotImplementedError

    def game_over(self, msg: Dict[str, Any]) -> None:
        pass

    def close(self) -> None:
        pass


class LocalPlayer(Player):
    def __init__(self, bot_name: str, profile) -> None:
        self.name = bot_name
        self.bot = REFERENCE_BOTS[bot_name](profile)

    def decide(self, msg: Dict[str, Any]) -> Tuple[int, Optional[str]]:
        action = self.bot.decide(SeatView(msg))
        if action not in [a["id"] for a in msg["legal"]]:
            raise RuntimeError("reference bot %s returned an illegal action %r" % (self.name, action))
        return action, None


class ProcessPlayer(Player):
    """A bot that runs as its own program, spoken to over stdin and stdout."""

    def __init__(
        self,
        command: str,
        table_id: str,
        *,
        decision_timeout_s: float = DEFAULT_DECISION_TIMEOUT_S,
        handshake_timeout_s: float = DEFAULT_HANDSHAKE_TIMEOUT_S,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> None:
        self.command = command
        self.name = command
        self.table_id = table_id
        self.decision_timeout_s = decision_timeout_s
        self.handshake_timeout_s = handshake_timeout_s
        self._lines: "queue.Queue[Optional[str]]" = queue.Queue()
        self._stderr_tail: List[str] = []
        self.bot_info: Dict[str, Any] = {}
        # Every process gets a new empty directory to be its HOME, its temp directory and (unless the run
        # names a directory to start in) its working directory. It is deleted when the process is stopped,
        # so nothing a bot writes in one game is there in the next, or at its other seat.
        self._scratch = tempfile.mkdtemp(prefix="hkbench-bot-")
        argv = shlex.split(command)
        if cwd is None:
            argv = [_absolute_if_file(a) for a in argv]  # a relative script path must still find its script
        child_env = bot_environment(extra=env, scratch=self._scratch)
        group = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if sys.platform == "win32" \
            else {"start_new_session": True}  # its own group, so the whole tree can be stopped
        self._readers: List[threading.Thread] = []
        try:
            self.proc = subprocess.Popen(
                argv,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd or self._scratch,
                env=child_env,
                universal_newlines=True,
                bufsize=1,
                **group,
            )
        except (OSError, ValueError) as exc:
            shutil.rmtree(self._scratch, ignore_errors=True)
            raise BotCrashed("could not start the bot: %s" % exc)
        for target in (self._read_stdout, self._read_stderr):
            t = threading.Thread(target=target, daemon=True)
            t.start()
            self._readers.append(t)
        try:
            self._handshake()
        except BaseException:
            self.close()
            raise

    # --- plumbing ---
    def _read_stdout(self) -> None:
        try:
            for line in self.proc.stdout:  # type: ignore[union-attr]
                self._lines.put(line)
        except (ValueError, OSError):
            pass
        finally:
            self._lines.put(None)

    def _read_stderr(self) -> None:
        try:
            for line in self.proc.stderr:  # type: ignore[union-attr]
                self._stderr_tail.append(line)
                del self._stderr_tail[:-20]
        except (ValueError, OSError):
            pass

    def _send(self, obj: Dict[str, Any]) -> None:
        try:
            self.proc.stdin.write(json.dumps(obj, separators=(",", ":")) + "\n")  # type: ignore[union-attr]
            self.proc.stdin.flush()  # type: ignore[union-attr]
        except (BrokenPipeError, OSError, ValueError):
            raise BotCrashed(self._crash_text("the bot closed its input"))

    def _crash_text(self, what: str) -> str:
        tail = "".join(self._stderr_tail[-5:]).strip()
        return what + (" (last stderr: %s)" % tail[-400:] if tail else "")

    def _next_message(self, deadline: float) -> Optional[Dict[str, Any]]:
        """The next JSON object the bot printed, or None on timeout. Raises on exit."""
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            try:
                line = self._lines.get(timeout=remaining)
            except queue.Empty:
                return None
            if line is None:
                raise BotCrashed(self._crash_text("the bot's output ended"))
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except ValueError:
                return {"_malformed": line[:200]}
            if not isinstance(obj, dict):
                return {"_malformed": line[:200]}
            return obj

    def _handshake(self) -> None:
        self._send({"type": "hello", "protocol": PROTOCOL, "table": self.table_id,
                    "decision_timeout_s": self.decision_timeout_s})
        msg = self._next_message(time.monotonic() + self.handshake_timeout_s)
        if msg is None:
            self.close()
            raise BotCrashed("the bot did not answer hello within %.0f s" % self.handshake_timeout_s)
        if msg.get("type") != "ready" or msg.get("protocol", PROTOCOL) != PROTOCOL:
            self.close()
            raise BotCrashed("the bot's first message was not a ready message: %r" % (msg,))
        self.bot_info = {k: msg[k] for k in ("name", "version") if k in msg}
        if "name" in msg:
            self.name = str(msg["name"])

    # --- the protocol ---
    def decide(self, msg: Dict[str, Any]) -> Tuple[int, Optional[str]]:
        legal = [a["id"] for a in msg["legal"]]
        self._send(msg)
        deadline = time.monotonic() + self.decision_timeout_s
        seq = msg["seq"]
        while True:
            reply = self._next_message(deadline)
            if reply is None:
                return fallback_action(msg), "timeout"
            if "_malformed" in reply:
                return fallback_action(msg), "malformed"
            if reply.get("type") != "action":
                return fallback_action(msg), "malformed"
            if reply.get("seq") != seq:
                # A late answer to an earlier decision. Ignore it and keep waiting.
                if isinstance(reply.get("seq"), int) and reply["seq"] < seq:
                    continue
                return fallback_action(msg), "malformed"
            action = reply.get("id")
            if isinstance(action, bool) or not isinstance(action, int):
                return fallback_action(msg), "malformed"
            if action not in legal:
                return fallback_action(msg), "illegal"
            return action, None

    def game_over(self, msg: Dict[str, Any]) -> None:
        self._send(msg)

    def _kill_tree(self) -> None:
        """Stop the bot and everything it started. Safe to call when it is already gone."""
        proc = self.proc
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
        else:
            try:
                os.killpg(proc.pid, signal.SIGKILL)  # the group this process leads, descendants included
            except (ProcessLookupError, PermissionError):
                pass
        try:
            proc.kill()
        except OSError:
            pass

    def close(self) -> None:
        if getattr(self, "_closed", False):
            return
        self._closed = True
        proc = self.proc
        if proc.poll() is None:
            try:
                self._send({"type": "bye"})
            except BotCrashed:
                pass
            try:
                proc.stdin.close()  # type: ignore[union-attr]
            except Exception:
                pass
            try:
                proc.wait(timeout=BYE_GRACE_S)
            except subprocess.TimeoutExpired:
                pass
        # Whether or not it left, nothing it started may stay: a descendant would hold the pipes and carry
        # state into the next game.
        self._kill_tree()
        try:
            proc.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            pass
        # With the tree gone the readers see the end of the pipes. Closing a pipe a reader is still inside would
        # wait for it, so a reader that has not finished in a second is left to die with the process.
        for t in self._readers:
            t.join(timeout=1.0)
        if not any(t.is_alive() for t in self._readers):
            for pipe in (proc.stdin, proc.stdout, proc.stderr):
                try:
                    pipe.close()  # type: ignore[union-attr]
                except Exception:
                    pass
        shutil.rmtree(self._scratch, ignore_errors=True)


def _absolute_if_file(token: str) -> str:
    """A command-line word that names a file here, as an absolute path (the bot starts in an empty directory)."""
    try:
        if not token.startswith("-") and os.path.isfile(token):
            return os.path.abspath(token)
    except (OSError, ValueError):
        pass
    return token


def make_player(spec: str, table_id: str, profile, *, decision_timeout_s: float = DEFAULT_DECISION_TIMEOUT_S,
                cwd: Optional[str] = None, env: Optional[Dict[str, str]] = None) -> Player:
    """``ref:<name>`` is an in-repo bot; anything else is a command to start."""
    if spec.startswith("ref:"):
        name = spec[4:]
        if name not in REFERENCE_BOTS:
            raise ValueError("no reference bot called %r (have: %s)" % (name, ", ".join(sorted(REFERENCE_BOTS))))
        return LocalPlayer(name, profile)
    return ProcessPlayer(spec, table_id, decision_timeout_s=decision_timeout_s, cwd=cwd, env=env)
