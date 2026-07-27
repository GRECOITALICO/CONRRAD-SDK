import sys

def notify_update_silently():
    try:
        from conrrad_sdk.runtime.version_manager import VersionManager
        manager = VersionManager()
        if manager.has_update():
            print(f"\n🔔 Conrrad update available ({manager.latest_version()})")
            print("👉 Run: conrrad upgrade\n")
    except Exception:
        pass

def main():
    if len(sys.argv) < 2:
        print("Usage: conrrad [new hello | run | init | doctor | ...]")
        print("Quick Start: conrrad new hello && cd hello && conrrad run")
        notify_update_silently()
        return

    cmd = sys.argv[1]

    if cmd == "init":
        from conrrad_sdk.cli.init import main as run
    elif cmd == "install":
        from conrrad_sdk.cli.install import main as run
    elif cmd == "synthetic":
        from conrrad_sdk.cli.synthetic import main as run
        sys.argv = sys.argv[2:] or ["run", "all"]
    elif cmd == "new":
        from conrrad_sdk.cli.new import main as run
    elif cmd == "doctor":
        from conrrad_sdk.cli.doctor import main as run
    elif cmd == "status":
        from conrrad_sdk.cli.status import main as run
    elif cmd == "demo":
        from conrrad_sdk.cli.demo import main as run
    elif cmd == "cloud":
        from conrrad_sdk.cli.cloud import main as run
    elif cmd == "dashboard":
        from conrrad_sdk.cli.dashboard import main as run
    elif cmd == "upgrade":
        from conrrad_sdk.cli.upgrade import main as run
    elif cmd == "run":
        from conrrad_sdk.cli.run import main as run
    elif cmd == "export":
        from conrrad_sdk.cli.export import main as run
    elif cmd == "birth":
        from conrrad_sdk.cli.birth import main as run
    elif cmd == "runtime":
        from conrrad_sdk.cli.runtime import main as run
    elif cmd == "--help":
        print("Usage: conrrad [init|new|birth|runtime|doctor|status|demo|cloud|dashboard|upgrade|run <project>|export <project>]")
        notify_update_silently()
        return 0
    else:
        print(f"Unknown command: {cmd}")
        return 1

    code = run()
    if cmd != "upgrade":
        notify_update_silently()
    sys.exit(code)

if __name__ == "__main__":
    main()
